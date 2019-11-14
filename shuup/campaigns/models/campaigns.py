# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import random
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum
from parler.models import TranslatableModel, TranslatedFields

from shuup.campaigns.consts import (
    CAMPAIGNS_CACHE_NAMESPACE, CATALOG_FILTER_CACHE_NAMESPACE,
    CONTEXT_CONDITION_CACHE_NAMESPACE
)
from shuup.campaigns.models.basket_conditions import (
    CategoryProductsBasketCondition, ProductsInBasketCondition
)
from shuup.campaigns.utils.campaigns import (
    get_lines_suppliers, get_product_ids_and_quantities
)
from shuup.campaigns.utils.matcher import get_matching_for_product
from shuup.core import cache
from shuup.core.fields import InternalIdentifierField
from shuup.core.models import Category, Order, Shop
from shuup.core.utils import context_cache
from shuup.utils.analog import define_log_model
from shuup.utils.django_compat import force_text
from shuup.utils.properties import MoneyPropped


class CampaignType(Enum):
    CATALOG = 1
    BASKET = 2


class CampaignQueryset(models.QuerySet):
    def available(self, shop=None):
        query = Q(
            Q(active=True) &
            (Q(start_datetime__isnull=True) | Q(start_datetime__lte=now())) &
            (Q(end_datetime__isnull=True) | Q(end_datetime__gte=now()))
        )
        if shop:
            query &= Q(shop=shop)
        return self.filter(query)


class Campaign(MoneyPropped, TranslatableModel):
    admin_url_suffix = None

    shop = models.ForeignKey(
        on_delete=models.CASCADE, to=Shop, verbose_name=_("shop"),
        help_text=_("The shop where the campaign is active."))
    name = models.CharField(max_length=120, verbose_name=_("name"), help_text=_("The name for this campaign."))

    # translations in subclass
    identifier = InternalIdentifierField(unique=True)

    active = models.BooleanField(default=False, verbose_name=_("active"), help_text=_(
        "Enable this if the campaign is currently active. Please also set a start and an end date."
    ))
    start_datetime = models.DateTimeField(null=True, blank=True, verbose_name=_("start date and time"), help_text=_(
        "The date and time the campaign starts. This is only applicable if the campaign is marked as active."
    ))
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name=_("end date and time"), help_text=_(
        "The date and time the campaign ends. This is only applicable if the campaign is marked as active."
    ))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL,
        verbose_name=_("created by"))
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL,
        verbose_name=_("modified by"))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))

    objects = CampaignQueryset.as_manager()

    class Meta:
        abstract = True
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')

    def save(self, *args, **kwargs):
        super(Campaign, self).save(*args, **kwargs)
        cache.bump_version(CAMPAIGNS_CACHE_NAMESPACE)
        cache.bump_version(CONTEXT_CONDITION_CACHE_NAMESPACE)
        cache.bump_version(CATALOG_FILTER_CACHE_NAMESPACE)

    def is_available(self):
        if not self.active:  # move to manager?
            return False
        if self.start_datetime and self.end_datetime:
            if self.start_datetime <= now() <= self.end_datetime:
                return True
            return False
        elif self.start_datetime and not self.end_datetime:
            if self.start_datetime > now():
                return False
        elif not self.start_datetime and self.end_datetime:
            if self.end_datetime < now():
                return False
        return True

    @property
    def type(self):
        return CampaignType.BASKET if isinstance(self, BasketCampaign) else CampaignType.CATALOG


class CatalogCampaign(Campaign):
    _queryset = None

    admin_url_suffix = "catalog_campaign"
    conditions = models.ManyToManyField('ContextCondition', blank=True, related_name='campaign')
    filters = models.ManyToManyField('CatalogFilter', blank=True, related_name='campaign')

    translations = TranslatedFields(public_name=models.CharField(max_length=120, blank=True, help_text=_(
        "The campaign name to show in the store front."
    )))

    def __str__(self):
        return force_text(_("Catalog Campaign: %(name)s" % dict(name=self.name)))

    def save(self, *args, **kwargs):
        super(CatalogCampaign, self).save(*args, **kwargs)
        self.filters.update(active=self.active)
        for f in self.filters.all():
            for matching_product in f.get_matching_shop_products():
                context_cache.bump_cache_for_shop_product(matching_product)
        self.conditions.update(active=self.active)

    def rules_match(self, context, shop_product, matching_catalog_filters, matching_context_conditions):
        if not self.is_available():
            return False

        # If rule has filters, all of them has to match
        for filter_pk in self.filters.values_list("pk", flat=True):
            if filter_pk not in matching_catalog_filters:
                return False

        # All filters match so let's check that also all the conditions match
        for condition_pk in self.conditions.values_list("pk", flat=True):
            if condition_pk not in matching_context_conditions:
                return False
        return True

    @classmethod
    def get_for_product(cls, shop_product):
        matching_filters = get_matching_for_product(shop_product, provide_category="campaign_catalog_filter")
        matching_conditions = get_matching_for_product(shop_product, provide_category="campaign_context_condition")
        query_filter = Q(Q(filters__in=matching_filters) | Q(conditions__in=matching_conditions))
        return cls.objects.available(shop=shop_product.shop).filter(query_filter).distinct()

    @classmethod
    def get_matching(cls, context, shop_product):
        prod_ctx_cache_elements = dict(
            customer=context.customer.pk or 0,
            shop=context.shop.pk,
            product_id=shop_product.pk)
        namespace = CAMPAIGNS_CACHE_NAMESPACE
        key = "%s:%s" % (namespace, hash(frozenset(prod_ctx_cache_elements.items())))
        cached_matching = cache.get(key, None)
        if cached_matching is not None:
            return cached_matching

        from shuup.campaigns.models.matching import get_matching_context_conditions, get_matching_catalog_filters
        matching_context_conditions = get_matching_context_conditions(context)
        matching_catalog_filters = get_matching_catalog_filters(shop_product)

        if not (matching_context_conditions or matching_catalog_filters):
            return []

        # Get all possible campaign id's for matching context_conditions
        campaigns_based_on_conditions = set(
            cls.objects.filter(
                active=True,
                shop=context.shop,
                conditions__id__in=matching_context_conditions
            ).values_list("pk", flat=True)
        )

        campaigns_based_on_catalog_filters = set()
        if hasattr(cls, "filters"):
            # Get all possible campaigns for matching catalog_filters
            campaigns_based_on_catalog_filters = set(
                cls.objects.filter(
                    active=True,
                    shop=context.shop,
                    filters__id__in=matching_catalog_filters
                ).values_list("pk", flat=True)
            )

        all_possible_campaigns_ids = (campaigns_based_on_conditions | campaigns_based_on_catalog_filters)
        matching = []
        for campaign in cls.objects.filter(id__in=all_possible_campaigns_ids):
            if campaign.rules_match(context, shop_product, matching_catalog_filters, matching_context_conditions):
                matching.append(campaign)
        cache.set(key, matching, timeout=None)
        return matching


class BasketCampaign(Campaign):
    admin_url_suffix = "basket_campaign"

    basket_line_text = models.CharField(
        max_length=120, verbose_name=_("basket line text"), help_text=_("This text will be shown in a basket."))

    conditions = models.ManyToManyField('BasketCondition', blank=True, related_name='campaign')
    coupon = models.OneToOneField('Coupon', null=True, blank=True, related_name='campaign', verbose_name=_("coupon"),
                                  on_delete=models.CASCADE)
    supplier = models.ForeignKey(
        "shuup.Supplier",
        null=True, blank=True,
        related_name="basket_campaigns",
        verbose_name=_("supplier"),
        help_text=_(
            "When set, this campaign will match only products from the selected supplier. "
            "Rules and Effects will also be restricted to include only the products of this supplier."
        ),
        on_delete=models.CASCADE,
    )

    translations = TranslatedFields(
        public_name=models.CharField(max_length=120, verbose_name=_("public name"), help_text=_(
            "The campaign name to show in the store front."
        ))
    )

    def __str__(self):
        return force_text(_("Basket Campaign: %(name)s" % dict(name=self.name)))

    def save(self, *args, **kwargs):
        if self.coupon:
            code_count_for_shop = BasketCampaign.objects.filter(
                active=True, shop_id=self.shop.id, coupon__code=self.coupon.code)
            if not self.id and code_count_for_shop.exists():
                raise ValidationError(_("Can't have multiple active campaigns with same code."))

            if self.id and code_count_for_shop.exclude(coupon_id=self.coupon.id).exists():
                raise ValidationError(_("Can't have multiple active campaigns with same code."))

        super(BasketCampaign, self).save(*args, **kwargs)
        self.conditions.update(active=self.active)

    @classmethod
    def get_for_product(cls, shop_product):
        matching_conditions = get_matching_for_product(
            shop_product, provide_category="campaign_basket_condition")
        matching_effects = get_matching_for_product(
            shop_product, provide_category="campaign_basket_discount_effect_form")
        matching_line_effects = get_matching_for_product(
            shop_product, provide_category="campaign_basket_line_effect_form")
        effects_q = Q(Q(line_effects__id__in=matching_line_effects) | Q(discount_effects__id__in=matching_effects))
        matching_q = Q(Q(conditions__in=matching_conditions) | effects_q)
        return cls.objects.available(shop=shop_product.shop).filter(matching_q).distinct()

    @classmethod
    def get_matching(cls, basket, lines):
        matching = []
        exclude_condition_ids = set()
        product_id_to_qty = get_product_ids_and_quantities(basket)
        lines_suppliers = get_lines_suppliers(basket)

        # Get ProductsInBasketCondition's that can't match with the basket
        products_in_basket_conditions_to_check = set(
            ProductsInBasketCondition.objects.filter(
                products__id__in=product_id_to_qty.keys()
            ).values_list("id", flat=True)
        )
        exclude_condition_ids |= set(
            ProductsInBasketCondition.objects.exclude(
                id__in=products_in_basket_conditions_to_check
            ).values_list("id", flat=True)
        )

        # Get CategoryProductsBasketCondition's that can't match with the basket
        categories = set(Category.objects.filter(
            shop_products__product_id__in=product_id_to_qty.keys()).values_list("id", flat=True))
        category_products_in_basket_to_check = set(
            CategoryProductsBasketCondition.objects.filter(categories__in=categories).values_list("id", flat=True)
        )
        exclude_condition_ids |= set(
            CategoryProductsBasketCondition.objects.exclude(
                id__in=category_products_in_basket_to_check
            ).values_list("id", flat=True)
        )

        queryset = cls.objects.filter(active=True, shop=basket.shop)

        if exclude_condition_ids:
            queryset = queryset.exclude(conditions__id__in=exclude_condition_ids)

        # exclude the campaigns that have supplier set and are not included the supplier list
        if lines_suppliers:
            queryset = queryset.filter(
                Q(supplier__isnull=True) | Q(supplier__in=lines_suppliers)
            )

        for campaign in queryset.prefetch_related("conditions").distinct():
            if campaign.rules_match(basket, lines):
                matching.append(campaign)

        return matching

    def rules_match(self, basket, lines):
        """
        Check if basket rules match.

        They will not match if:
        1) The campaign is not active
        2) The campaign has attached coupon,
           which doesn't match or is not active
        3) Any of the attached rules don't match
        """
        if not self.is_available():
            return False

        if self.coupon and not (self.coupon.active and self.coupon.code.upper() in [c.upper() for c in basket.codes]):
            return False

        for rule in self.conditions.all():
            if not rule.matches(basket, lines):
                return False
        return True


class CouponUsage(models.Model):
    coupon = models.ForeignKey(on_delete=models.CASCADE, to='Coupon', related_name='usages')
    order = models.ForeignKey(on_delete=models.CASCADE, to=Order, related_name='coupon_usages')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL,
        verbose_name=_("created by"))
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL,
        verbose_name=_("modified by"))

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))

    @classmethod
    def add_usage(cls, order, coupon):
        return cls.objects.create(order=order, coupon=coupon)


@python_2_unicode_compatible
class Coupon(models.Model):
    admin_url_suffix = "coupon"
    name_field = "code"  # TODO: Document me
    search_fields = ["code"]    # used by Select2Multiple to know which fields use to search by

    code = models.CharField(max_length=12)

    usage_limit_customer = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("usage limit per customer"), help_text=_("Limit the amount of usages per a single customer."))
    usage_limit = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("usage limit"),
        help_text=_("Set the absolute limit of usages for this coupon. "
                    "If the limit is zero (0), coupon can't be used."))

    active = models.BooleanField(default=False, verbose_name=_("is active"))
    shop = models.ForeignKey(
        on_delete=models.CASCADE, to="shuup.Shop", verbose_name=_("shop"), related_name="campaign_coupons",
        null=True, help_text=_("The shop where the coupon is active.")
    )
    supplier = models.ForeignKey(
        "shuup.Supplier",
        null=True, blank=True,
        related_name="campaign_coupons",
        verbose_name=_("supplier"),
        on_delete=models.CASCADE,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL,
        verbose_name=_("created by"))
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL,
        verbose_name=_("modified by"))

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))

    def save(self, **kwargs):
        campaign = BasketCampaign.objects.filter(active=True, coupon_id=self.id).first()
        if campaign and BasketCampaign.objects.filter(
                active=True, shop_id=campaign.shop.id, coupon__code=self.code).exclude(id=campaign.id).exists():
            raise ValidationError(_("Can not have multiple active campaigns with the same code."))

        return super(Coupon, self).save(**kwargs)

    @classmethod
    def generate_code(cls, length=6):
        if length > 12:
            length = 12
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

    @property
    def exhausted(self):
        val = bool(self.usage_limit and self.usages.count() >= self.usage_limit)
        return val

    @property
    def attached(self):
        return BasketCampaign.objects.filter(coupon=self).exists()

    def attach_to_campaign(self, campaign):
        if not self.attached:
            self.campaign = campaign

    @classmethod
    def is_usable(cls, code, customer):
        try:
            code = cls.objects.get(code__iexact=code, active=True)
            return code.can_use_code(customer)
        except cls.DoesNotExist:
            return False

    def can_use_code(self, customer):
        """
        Check if customer can use the code.

        :param customer:
        :type customer: `Contact` or None
        :rtype: True|False
        """
        if not self.active:
            return False

        if not self.attached:
            return False

        if self.usage_limit_customer:
            if not customer or customer.is_anonymous:
                return False
            if (self.usages.filter(order__customer=customer, coupon=self).count() >= self.usage_limit_customer):
                return False

        return not self.exhausted

    def use(self, order):
        return CouponUsage.add_usage(order=order, coupon=self)

    def increase_customer_usage_limit_by(self, amount):
        if self.usage_limit_customer:
            new_limit = self.usage_limit_customer + amount
        else:
            new_limit = self.usages.count() + amount
        self.usage_limit_customer = new_limit

    def increase_usage_limit_by(self, amount):
        self.usage_limit = self.usage_limit + amount if self.usage_limit else (self.usages.count() + amount)

    def has_been_used(self, usage_count=1):
        """ See if code was already used the number of maximum times given """
        return CouponUsage.objects.filter(coupon=self).count() >= usage_count

    def __str__(self):
        return self.code


CatalogCampaignLogEntry = define_log_model(CatalogCampaign)
BasketCampaignLogEntry = define_log_model(BasketCampaign)
CouponLogEntry = define_log_model(Coupon)
CouponUsageLogEntry = define_log_model(CouponUsage)
