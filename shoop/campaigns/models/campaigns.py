# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_text
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField, MoneyValueField
from shoop.core.models import Order, Shop, ShopProduct
from shoop.utils.properties import MoneyPropped, PriceProperty


class Campaign(MoneyPropped, TranslatableModel):
    admin_url_suffix = None

    shop = models.ForeignKey(Shop, verbose_name=_("shop"), help_text=_("The shop where campaign is active."))
    name = models.CharField(max_length=120, verbose_name=_("name"), help_text=_("The name for this campaign."))

    # translations in subclass

    identifier = InternalIdentifierField(unique=True)
    discount_percentage = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."))
    discount_amount = PriceProperty("discount_amount_value", "shop.currency", "shop.prices_include_tax")
    discount_amount_value = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("discount amount value"),
        help_text=_("Flat amount of discount. Mutually exclusive with percentage."))
    active = models.BooleanField(default=False, verbose_name=_("active"))
    start_datetime = models.DateTimeField(null=True, blank=True, verbose_name=_("start date and time"))
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name=_("end date and time"))
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

    # objects = CampaignManager()

    class Meta:
        abstract = True
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')

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

    def save(self, **kwargs):
        if self.discount_percentage and self.discount_amount_value:
            raise ValidationError(_("You should only define either discount percentage or amount."))

        if not (self.discount_percentage or self.discount_amount_value):
            raise ValidationError(_("You must define discount percentage or amount."))

        super(Campaign, self).save(**kwargs)


class CatalogCampaign(Campaign):
    _queryset = None

    admin_url_suffix = "catalog_campaigns"
    conditions = models.ManyToManyField('ContextCondition', blank=True, related_name='campaign')
    filters = models.ManyToManyField('CatalogFilter', blank=True, related_name='campaign')

    translations = TranslatedFields(public_name=models.CharField(max_length=120, blank=True))

    def __str__(self):
        return force_text(_("Catalog Campaign: %(name)s" % dict(name=self.name)))

    def rules_match(self, context, shop_product):
        if not self.is_available():
            return False

        if not self._queryset:
            queryset = ShopProduct.objects.filter(shop=self.shop)
            for catalog_filter in self.filters.all():
                queryset = catalog_filter.filter_queryset(queryset)
            self._queryset = queryset
        filters_match = self._queryset.filter(pk=shop_product.pk).exists()

        conditions_match = all(condition.matches(context) for condition in self.conditions.all())

        return (conditions_match and filters_match)

    @classmethod
    def get_matching(cls, context, product):
        matching = []
        for campaign in cls.objects.filter(active=True, shop=context.shop):
            if campaign.rules_match(context, product):
                matching.append(campaign)
        return matching


class BasketCampaign(Campaign):
    admin_url_suffix = "basket_campaigns"

    basket_line_text = models.CharField(
        max_length=120, verbose_name=_("basket line text"), help_text=_("This text will be shown in basket."))

    conditions = models.ManyToManyField('BasketCondition', blank=True, related_name='campaign')
    coupon = models.OneToOneField('Coupon', null=True, blank=True, related_name='campaign')

    translations = TranslatedFields(
        public_name=models.CharField(max_length=120)
    )

    def __str__(self):
        return force_text(_("Basket Campaign: %(name)s" % dict(name=self.name)))

    @classmethod
    def get_matching(cls, basket, lines):
        matching = []
        for campaign in cls.objects.filter(active=True, shop=basket.shop):
            if campaign.rules_match(basket, lines):
                matching.append(campaign)
        return matching

    def rules_match(self, basket, lines):
        """
        Check if basket rules match.

        They will not match if
        1) The campaign is not active
        2) The campaign has attached coupon
           which doesn't match or is not active
        3) Any of the attached rules doesn't match
        """
        if not self.is_available():
            return False

        if self.coupon and not self.coupon.active:
            return False

        matching_rules = [rule.matches(basket, lines) for rule in self.conditions.all()]

        if self.coupon:
            matching_rules.append((self.coupon.code in basket.codes))
        return all(matching_rules)


class CouponUsage(models.Model):
    coupon = models.ForeignKey('Coupon', related_name='usages')
    order = models.ForeignKey(Order, related_name='coupon_usages')

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


class Coupon(models.Model):
    admin_url_suffix = "coupons"

    code = models.CharField(max_length=12)

    usage_limit_customer = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("usage limit per customer"), help_text=_("Limit the amount of usages per a single customer."))
    usage_limit = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("usage limit"),
        help_text=_("Set the absolute limit of usages for this coupon. "
                    "If the limit is zero (0) coupon cannot be used."))

    active = models.BooleanField(default=False, verbose_name=_("is active"))

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
            code = cls.objects.get(code=code)
            return code.can_use_code(customer)
        except cls.DoesNotExist:
            return False

    def can_use_code(self, customer):
        """
        Check if customer can use the code

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
        """ See if code is used the times given """
        return CouponUsage.objects.filter(coupon=self).count() >= usage_count

    def save(self, **kwargs):
        if Coupon.objects.filter(code=self.code, active=True).exclude(pk=self.pk).exists():
            raise ValidationError(_("Cannot have two same codes active at the same time."))
        return super(Coupon, self).save(**kwargs)

    def __str__(self):
        return self.code
