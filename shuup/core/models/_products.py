# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import six
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.excs import ImpossibleProductModeException
from shuup.core.fields import InternalIdentifierField, MeasurementField
from shuup.core.signals import post_clean, pre_clean
from shuup.core.taxing import TaxableItem
from shuup.core.utils.slugs import generate_multilanguage_slugs
from shuup.utils.analog import define_log_model, LogEntryKind
from shuup.utils.django_compat import force_text

from ._attributes import AppliedAttribute, AttributableMixin, Attribute
from ._product_media import ProductMediaKind
from ._product_packages import ProductPackageLink
from ._product_variation import (
    get_all_available_combinations, get_combination_hash_from_variable_mapping,
    ProductVariationResult, ProductVariationVariable
)


# TODO (2.0): This should be extandable
class ProductMode(Enum):
    NORMAL = 0
    PACKAGE_PARENT = 1
    SIMPLE_VARIATION_PARENT = 2
    VARIABLE_VARIATION_PARENT = 3
    VARIATION_CHILD = 4
    SUBSCRIPTION = 5  # This is like package_parent and all the functionality is same under the hood.

    class Labels:
        NORMAL = _('normal')
        PACKAGE_PARENT = _('package parent')
        SIMPLE_VARIATION_PARENT = _('variation parent (simple)')
        VARIABLE_VARIATION_PARENT = _('variation parent (variable)')
        VARIATION_CHILD = _('variation child')
        SUBSCRIPTION = _('subscription')


class ProductVisibility(Enum):
    VISIBLE_TO_ALL = 1
    VISIBLE_TO_LOGGED_IN = 2
    VISIBLE_TO_GROUPS = 3

    class Labels:
        VISIBLE_TO_ALL = _('visible to all')
        VISIBLE_TO_LOGGED_IN = _('visible to logged in')
        VISIBLE_TO_GROUPS = _('visible to groups')


# Deprecated. Used in old migrations
class StockBehavior(Enum):
    UNSTOCKED = 0
    STOCKED = 1

    class Labels:
        STOCKED = _('stocked')
        UNSTOCKED = _('unstocked')


class ProductCrossSellType(Enum):
    RECOMMENDED = 1
    RELATED = 2
    COMPUTED = 3
    BOUGHT_WITH = 4

    class Labels:
        RECOMMENDED = _('recommended')
        RELATED = _('related')
        COMPUTED = _('computed')
        BOUGHT_WITH = _('bought with')


class ShippingMode(Enum):
    NOT_SHIPPED = 0
    SHIPPED = 1

    class Labels:
        NOT_SHIPPED = _('not shipped (non-deliverable)')
        SHIPPED = _('shipped (deliverable)')


class ProductVerificationMode(Enum):
    NO_VERIFICATION_REQUIRED = 0
    ADMIN_VERIFICATION_REQUIRED = 1
    THIRD_PARTY_VERIFICATION_REQUIRED = 2

    class Labels:
        NO_VERIFICATION_REQUIRED = _('no verification required')
        ADMIN_VERIFICATION_REQUIRED = _('admin verification required')
        THIRD_PARTY_VERIFICATION_REQUIRED = _('third party verification required')


@python_2_unicode_compatible
class ProductType(TranslatableModel):
    identifier = InternalIdentifierField(unique=True)
    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_('name'), help_text=_(
                "Enter a descriptive name for your product type. "
                "Products and attributes for products of this type can be found under this name."
            )
        ),
    )
    attributes = models.ManyToManyField(
        "Attribute", blank=True, related_name='product_types',
        verbose_name=_('attributes'), help_text=_(
            "Select attributes that go with your product type. To change available attributes search for `Attributes`."
        )
    )

    class Meta:
        verbose_name = _('product type')
        verbose_name_plural = _('product types')

    def __str__(self):
        return force_text(self.safe_translation_getter("name") or self.identifier)


class ProductQuerySet(TranslatableQuerySet):

    def _select_related(self):
        return self.select_related(
            "primary_image",
            "sales_unit",
            "tax_class",
            "manufacturer"
        ).prefetch_related(
            "translations",
            "shop_products",
            "shop_products__display_unit",
            "shop_products__display_unit__internal_unit",
            "shop_products__display_unit__translations",
            "shop_products__categories",
            "shop_products__categories__translations",
            "shop_products__primary_category",
            "primary_image__file"
        )

    def _visible(self, shop, customer, language=None, invisible_modes=[ProductMode.VARIATION_CHILD]):
        root = (self.language(language) if language else self)
        qs = root.all().filter(shop_products__shop=shop)

        if customer and customer.is_all_seeing:
            if invisible_modes:
                qs = qs.exclude(mode__in=invisible_modes)
        else:
            from ._product_shops import ShopProductVisibility
            qs = qs.exclude(
                Q(shop_products__visibility=ShopProductVisibility.NOT_VISIBLE) |
                Q(shop_products__available_until__lte=now())
            )
            if invisible_modes:
                qs = qs.exclude(mode__in=invisible_modes)

            if customer and not customer.is_anonymous:
                visible_to_logged_in_q = Q(shop_products__visibility_limit__in=(
                    ProductVisibility.VISIBLE_TO_ALL, ProductVisibility.VISIBLE_TO_LOGGED_IN
                ))
                visible_to_my_groups_q = Q(
                    shop_products__visibility_limit=ProductVisibility.VISIBLE_TO_GROUPS,
                    shop_products__visibility_groups__in=customer.groups.all()
                )
                qs = qs.filter(visible_to_logged_in_q | visible_to_my_groups_q)
            else:
                qs = qs.filter(shop_products__visibility_limit=ProductVisibility.VISIBLE_TO_ALL)

        qs = qs.select_related(*Product.COMMON_SELECT_RELATED).distinct()
        return qs.exclude(deleted=True).exclude(type__isnull=True)

    def _get_qs(self, shop, customer, language, visibility_type):
        qs = self._visible(shop=shop, customer=customer, language=language)
        if customer and customer.is_all_seeing:
            return qs._select_related()
        else:
            from ._product_shops import ShopProductVisibility
            return qs.filter(
                shop_products__shop=shop,
                shop_products__visibility__in=(
                    visibility_type, ShopProductVisibility.ALWAYS_VISIBLE
                )
            )._select_related()

    def listed(self, shop, customer=None, language=None):
        from ._product_shops import ShopProductVisibility
        return self._get_qs(shop, customer, language, ShopProductVisibility.LISTED)

    def searchable(self, shop, customer=None, language=None):
        from ._product_shops import ShopProductVisibility
        return self._get_qs(shop, customer, language, ShopProductVisibility.SEARCHABLE)

    def visible(self, shop, customer=None, language=None):
        return self._visible(shop, customer=customer, language=language, invisible_modes=[])

    def all_except_deleted(self, language=None, shop=None):
        qs = (self.language(language) if language else self).exclude(deleted=True).exclude(type__isnull=True)
        if shop:
            qs = qs.filter(shop_products__shop=shop)
        qs = qs.select_related(*Product.COMMON_SELECT_RELATED)
        return qs


@python_2_unicode_compatible
class Product(TaxableItem, AttributableMixin, TranslatableModel):
    COMMON_SELECT_RELATED = ("type", "primary_image", "tax_class")

    # Metadata
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('modified on'))
    deleted = models.BooleanField(default=False, editable=False, db_index=True, verbose_name=_('deleted'))

    # Behavior
    mode = EnumIntegerField(ProductMode, default=ProductMode.NORMAL, verbose_name=_('mode'))
    variation_parent = models.ForeignKey(
        "self", null=True, blank=True, related_name='variation_children',
        on_delete=models.PROTECT,
        verbose_name=_('variation parent'))
    shipping_mode = EnumIntegerField(
        ShippingMode, default=ShippingMode.SHIPPED, verbose_name=_('shipping mode'),
        help_text=_("Set to `shipped` if the product requires shipment.")
    )
    sales_unit = models.ForeignKey(
        "SalesUnit", verbose_name=_('sales unit'), blank=True, null=True, on_delete=models.PROTECT, help_text=_(
            "Select a sales unit for your product. "
            "This is shown in your store front and is used to determine whether the product can be purchased using "
            "fractional amounts. To change settings search for `Sales Units`."
        )
    )
    tax_class = models.ForeignKey("TaxClass", verbose_name=_('tax class'), on_delete=models.PROTECT, help_text=_(
            "Select a tax class for your product. "
            "The tax class is used to determine which taxes to apply to your product. "
            "Define tax classes by searching for `Tax Classes`. "
            "To define the rules by which taxes are applied search for `Tax Rules`."
        )
    )

    # Identification
    type = models.ForeignKey(
        "ProductType", related_name='products',
        on_delete=models.SET_NULL, db_index=True,
        verbose_name=_('product type'),
        null=True,
        help_text=_(
            "Select a product type for your product. "
            "These allow you to configure custom attributes to help with classification and analysis."
        )
    )
    sku = models.CharField(
        db_index=True, max_length=128, verbose_name=_('SKU'), unique=True,
        help_text=_(
            "Enter a SKU (Stock Keeping Unit) number for your product. "
            "This is a product identification code that helps you track products through your inventory "
            "and analyze their movement. People often use the product's barcode number, "
            "but you can set up any numerical system you want to keep track of products."
        )
    )
    gtin = models.CharField(blank=True, max_length=40, verbose_name=_('GTIN'), help_text=_(
        "You can enter a Global Trade Item Number. "
        "This is typically a 14 digit identification number for all of your trade items. "
        "It can often be found by the barcode."
    ))
    barcode = models.CharField(blank=True, max_length=40, verbose_name=_('barcode'), help_text=_(
        "You can enter the barcode number for your product. This is useful for inventory/stock tracking and analysis."
    ))
    accounting_identifier = models.CharField(max_length=32, blank=True, verbose_name=_('bookkeeping account'))
    profit_center = models.CharField(max_length=32, verbose_name=_('profit center'), blank=True)
    cost_center = models.CharField(max_length=32, verbose_name=_('cost center'), blank=True)

    # Physical dimensions
    width = MeasurementField(
        unit=settings.SHUUP_LENGTH_UNIT,
        verbose_name=_('width ({})'.format(settings.SHUUP_LENGTH_UNIT)),
        help_text=_(
            "Set the measured width of your product or product packaging. "
            "This will provide customers with the product size and help with calculating shipping costs."
        )
    )
    height = MeasurementField(
        unit=settings.SHUUP_LENGTH_UNIT,
        verbose_name=_('height ({})'.format(settings.SHUUP_LENGTH_UNIT)),
        help_text=_(
            "Set the measured height of your product or product packaging. "
            "This will provide customers with the product size and help with calculating shipping costs."
        )
    )
    depth = MeasurementField(
        unit=settings.SHUUP_LENGTH_UNIT,
        verbose_name=_('depth ({})'.format(settings.SHUUP_LENGTH_UNIT)),
        help_text=_(
            "Set the measured depth or length of your product or product packaging. "
            "This will provide customers with the product size and help with calculating shipping costs."
        )
    )
    net_weight = MeasurementField(
        unit=settings.SHUUP_MASS_UNIT,
        verbose_name=_('net weight ({})'.format(settings.SHUUP_MASS_UNIT)),
        help_text=_(
            "Set the measured weight of your product WITHOUT its packaging. "
            "This will provide customers with the actual product's weight."
        )
    )
    gross_weight = MeasurementField(
        unit=settings.SHUUP_MASS_UNIT,
        verbose_name=_('gross weight ({})'.format(settings.SHUUP_MASS_UNIT)),
        help_text=_(
            "Set the measured gross weight of your product WITH its packaging. "
            "This will help with calculating shipping costs."
        )
    )

    # Misc.
    manufacturer = models.ForeignKey(
        "Manufacturer", blank=True, null=True,
        verbose_name=_('manufacturer'), on_delete=models.PROTECT, help_text=_(
            "Select a manufacturer for your product. To define these, search for `Manufacturers`."
        )
    )
    primary_image = models.ForeignKey(
        "ProductMedia", null=True, blank=True,
        related_name="primary_image_for_products",
        on_delete=models.SET_NULL,
        verbose_name=_("primary image"))

    translations = TranslatedFields(
        name=models.CharField(
            max_length=256, verbose_name=_('name'), db_index=True,
            help_text=_("Enter a descriptive name for your product. This will be its title in your store front.")),
        description=models.TextField(
            blank=True, verbose_name=_('description'),
            help_text=_(
                "To make your product stand out, give it an awesome description. "
                "This is what will help your shoppers learn about your products. "
                "It will also help shoppers find them in the store and on the web."
            )
        ),
        short_description=models.CharField(
            max_length=150, blank=True, verbose_name=_('short description'),
            help_text=_(
                "Enter a short description for your product. The short description will "
                "be used to get the attention of your customer with a small, but "
                "precise description of your product. It also helps with getting more "
                "traffic via search engines."
            )
        ),
        slug=models.SlugField(
            verbose_name=_('slug'), max_length=255, blank=True, null=True,
            help_text=_(
                "Enter a URL slug for your product. Slug is user- and search engine-friendly short text "
                "used in a URL to identify and describe a resource. In this case it will determine "
                "what your product page URL in the browser address bar will look like. "
                "A default will be created using the product name."
            )
        ),
        keywords=models.TextField(blank=True, verbose_name=_('keywords'), help_text=_(
                "You can enter keywords that describe your product. "
                "This will help your shoppers learn about your products. "
                "It will also help shoppers find them in the store and on the web."
            )
        ),
        variation_name=models.CharField(
            max_length=128, blank=True,
            verbose_name=_('variation name'),
            help_text=_(
                "You can enter a name for the variation of your product. "
                "This could be for example different colors, sizes or versions. "
                "To manage variations, at the top of the the individual product page, "
                "click `Actions` -> `Manage Variations`."
            )
        )
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ('-id',)
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        try:
            return u"%s" % self.name
        except ObjectDoesNotExist:
            return self.sku

    def get_shop_instance(self, shop, allow_cache=False):
        """
        :type shop: shuup.core.models.Shop
        :rtype: shuup.core.models.ShopProduct
        """

        from shuup.core.utils import context_cache
        key, val = context_cache.get_cached_value(
            identifier="shop_product",
            item=self,
            context={"shop": shop},
            allow_cache=allow_cache
        )
        if val is not None:
            return val

        shop_inst = self.shop_products.get(shop_id=shop.id)
        context_cache.set_cached_value(key, shop_inst)
        return shop_inst

    def get_priced_children(self, context, quantity=1):
        """
        Get child products with price infos sorted by price.

        :rtype: list[(Product,PriceInfo)]
        :return:
          List of products and their price infos sorted from cheapest to
          most expensive.
        """
        from shuup.core.models import ShopProduct
        priced_children = []
        shop_product_query = Q(
            shop=context.shop,
            product_id__in=self.variation_children.visible(
                shop=context.shop, customer=context.customer).values_list("id", flat=True)
        )

        for shop_product in ShopProduct.objects.filter(shop_product_query):
            if shop_product.is_orderable(supplier=None, customer=context.customer, quantity=1):
                child = shop_product.product
                priced_children.append((child, child.get_price_info(context, quantity=quantity)))

        return sorted(priced_children, key=(lambda x: x[1].price))

    def get_cheapest_child_price(self, context, quantity=1):
        price_info = self.get_cheapest_child_price_info(context, quantity)
        if price_info:
            return price_info.price

    def get_child_price_range(self, context, quantity=1):
        """
        Get the prices for cheapest and the most expensive child.

        The attribute used for sorting is `PriceInfo.price`.

        Return (`None`, `None`) if `self.variation_children` do not exist.
        This is because we cannot return anything sensible.

        :type context: shuup.core.pricing.PricingContextable
        :type quantity: int
        :return: a tuple of prices.
        :rtype: (shuup.core.pricing.Price, shuup.core.pricing.Price)
        """
        items = []
        for child in self.variation_children.visible(shop=context.shop, customer=context.customer):
            items.append(child.get_price_info(context, quantity=quantity))

        if not items:
            return (None, None)

        infos = sorted(items, key=lambda x: x.price)
        return (infos[0].price, infos[-1].price)

    def get_cheapest_child_price_info(self, context, quantity=1):
        """
        Get the `PriceInfo` of the cheapest variation child.

        The attribute used for sorting is `PriceInfo.price`.

        Return `None` if `self.variation_children` do not exist.
        This is because we cannot return anything sensible.

        :type context: shuup.core.pricing.PricingContextable
        :rtype: shuup.core.pricing.PriceInfo
        """
        items = []
        for child in self.variation_children.visible(shop=context.shop, customer=context.customer):
            items.append(child.get_price_info(context, quantity=quantity))

        if not items:
            return None

        return sorted(items, key=lambda x: x.price)[0]

    def get_price_info(self, context, quantity=1):
        """
        Get `PriceInfo` object for the product in given context.

        Returned `PriceInfo` object contains calculated `price` and
        `base_price`.  The calculation of prices is handled in the
        current pricing module.

        :type context: shuup.core.pricing.PricingContextable
        :rtype: shuup.core.pricing.PriceInfo
        """
        from shuup.core.pricing import get_price_info
        return get_price_info(product=self, context=context, quantity=quantity)

    def get_price(self, context, quantity=1):
        """
        Get price of the product within given context.

        .. note::

           When the current pricing module implements pricing steps, it
           is possible that ``p.get_price(ctx) * 123`` is not equal to
           ``p.get_price(ctx, quantity=123)``, since there could be
           quantity discounts in effect, but usually they are equal.

        :type context: shuup.core.pricing.PricingContextable
        :rtype: shuup.core.pricing.Price
        """
        return self.get_price_info(context, quantity).price

    def get_base_price(self, context, quantity=1):
        """
        Get base price of the product within given context.

        Base price differs from the (effective) price when there are
        discounts in effect.

        :type context: shuup.core.pricing.PricingContextable
        :rtype: shuup.core.pricing.Price
        """
        return self.get_price_info(context, quantity=quantity).base_price

    def get_available_attribute_queryset(self):
        if self.type_id:
            return self.type.attributes.visible()
        else:
            return Attribute.objects.none()

    def get_available_variation_results(self):
        """
        Get a dict of `combination_hash` to product ID of variable variation results.

        :return: Mapping of combination hashes to product IDs.
        :rtype: dict[str, int]
        """
        return dict(
            ProductVariationResult.objects.filter(product=self).filter(status=1)
            .values_list("combination_hash", "result_id")
        )

    def get_all_available_combinations(self):
        """
        Generate all available combinations of variation variables.

        If the product is not a variable variation parent, the iterator is empty.

        Because of possible combinatorial explosion this is a generator function.
        (For example 6 variables with 5 options each, would explode to 15,625 combinations.)

        :return: Iterable of combination information dicts.
        :rtype: Iterable[dict]
        """
        return get_all_available_combinations(self)

    def clear_variation(self):
        """
        Fully remove variation information.

        Make this product a non-variation parent.
        """
        self.simplify_variation()
        for child in self.variation_children.all():
            if child.variation_parent_id == self.pk:
                child.unlink_from_parent()
        self.verify_mode()
        self.save()

    def simplify_variation(self):
        """
        Remove variation variables from a given variation parent, turning it
        into a simple variation (or a normal product, if it has no children).

        :param product: Variation parent, that shouldn't be variable any more.
        :type product: shuup.core.models.Product
        """
        ProductVariationVariable.objects.filter(product=self).delete()
        ProductVariationResult.objects.filter(product=self).delete()
        self.verify_mode()
        self.save()

    @staticmethod
    def _get_slug_name(self, translation=None):
        if self.deleted:
            return None
        return getattr(translation, "name", self.sku)

    def save(self, *args, **kwargs):
        self.clean()
        if self.net_weight and self.net_weight > 0:
            self.gross_weight = max(self.net_weight, self.gross_weight)
        rv = super(Product, self).save(*args, **kwargs)
        generate_multilanguage_slugs(self, self._get_slug_name)
        return rv

    def clean(self):
        pre_clean.send(type(self), instance=self)
        super(Product, self).clean()
        post_clean.send(type(self), instance=self)

    def delete(self, using=None):
        raise NotImplementedError("Error! Not implemented: `Product` -> `delete()`. Use `soft_delete()` for products.")

    def soft_delete(self, user=None):
        if not self.deleted:
            self.deleted = True
            self.add_log_entry("Success! Deleted (soft).", kind=LogEntryKind.DELETION, user=user)
            # Bypassing local `save()` on purpose.
            super(Product, self).save(update_fields=("deleted",))

    def verify_mode(self):
        if ProductPackageLink.objects.filter(parent=self).exists():
            self.mode = ProductMode.PACKAGE_PARENT
            self.external_url = None
            self.variation_children.clear()
        elif ProductVariationVariable.objects.filter(product=self).exists():
            self.mode = ProductMode.VARIABLE_VARIATION_PARENT
        elif self.variation_children.exists():
            if ProductVariationResult.objects.filter(product=self).exists():
                self.mode = ProductMode.VARIABLE_VARIATION_PARENT
            else:
                self.mode = ProductMode.SIMPLE_VARIATION_PARENT
            self.external_url = None
            ProductPackageLink.objects.filter(parent=self).delete()
        elif self.variation_parent:
            self.mode = ProductMode.VARIATION_CHILD
            ProductPackageLink.objects.filter(parent=self).delete()
            self.variation_children.clear()
            self.external_url = None
        else:
            self.mode = ProductMode.NORMAL

    def unlink_from_parent(self):
        if self.variation_parent:
            parent = self.variation_parent
            self.variation_parent = None
            self.save()
            parent.verify_mode()
            self.verify_mode()
            self.save()
            ProductVariationResult.objects.filter(result=self).delete()
            return True

    def link_to_parent(self, parent, variables=None, combination_hash=None):
        """
        :param parent: The parent to link to.
        :type parent: Product
        :param variables: Optional dict of {variable identifier: value identifier} for a complex variable linkage.
        :type variables: dict|None
        :param combination_hash: Optional combination hash (for variable variations), if precomputed. Mutually
                                 exclusive with `variables`.
        :type combination_hash: str|None
        """
        if combination_hash:
            if variables:
                raise ValueError("Error! `combination_hash` and `variables` are mutually exclusive.")
            variables = True  # Simplifies the below invariant checks

        self._raise_if_cant_link_to_parent(parent, variables)

        self.unlink_from_parent()
        self.variation_parent = parent
        self.verify_mode()
        self.save()
        if not parent.is_variation_parent():
            parent.verify_mode()
            parent.save()

        if variables:
            if not combination_hash:  # No precalculated hash, need to figure that out
                combination_hash = get_combination_hash_from_variable_mapping(parent, variables=variables)

            pvr = ProductVariationResult.objects.create(
                product=parent,
                combination_hash=combination_hash,
                result=self
            )
            if parent.mode == ProductMode.SIMPLE_VARIATION_PARENT:
                parent.verify_mode()
                parent.save()
            return pvr
        else:
            return True

    def _raise_if_cant_link_to_parent(self, parent, variables):
        """
        Validates relation possibility for `self.link_to_parent()`.

        :param parent: parent product of self.
        :type parent: Product
        :param variables:
        :type variables: dict|None
        """
        if parent.is_variation_child():
            raise ImpossibleProductModeException(
                _("Multilevel parentage hierarchies aren't supported (parent is a child already)."),
                code="multilevel"
            )
        if parent.mode == ProductMode.VARIABLE_VARIATION_PARENT and not variables:
            raise ImpossibleProductModeException(
                _("Parent is a variable variation parent, yet variables were not passed."),
                code="no_variables"
            )
        if parent.mode == ProductMode.SIMPLE_VARIATION_PARENT and variables:
            raise ImpossibleProductModeException(
                "Error! Parent is a simple variation parent, yet variables were passed.",
                code="extra_variables"
            )
        if self.mode == ProductMode.SIMPLE_VARIATION_PARENT:
            raise ImpossibleProductModeException(
                _("Multilevel parentage hierarchies aren't supported (this product is a simple variation parent)."),
                code="multilevel"
            )
        if self.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            raise ImpossibleProductModeException(
                _("Multilevel parentage hierarchies aren't supported (this product is a variable variation parent)."),
                code="multilevel"
            )

    def make_package(self, package_def):
        if self.mode != ProductMode.NORMAL:
            raise ImpossibleProductModeException(
                _("Product is currently not a normal product, and can't be turned into a package."),
                code="abnormal"
            )

        for child_product, quantity in six.iteritems(package_def):
            if child_product.pk == self.pk:
                raise ImpossibleProductModeException(_("Package can't contain itself."), code="content")
            # :type child_product: Product
            if child_product.is_variation_parent():
                raise ImpossibleProductModeException(
                    _("Variation parents can't belong in the package."),
                    code="abnormal"
                )
            if child_product.is_container():
                raise ImpossibleProductModeException(_("Packages can't be nested."), code="multilevel")
            if quantity <= 0:
                raise ImpossibleProductModeException(_("Quantity %s is invalid.") % quantity, code="quantity")
            ProductPackageLink.objects.create(parent=self, child=child_product, quantity=quantity)
        self.verify_mode()

    def get_package_child_to_quantity_map(self):
        if self.is_container():
            product_id_to_quantity = dict(
                ProductPackageLink.objects.filter(parent=self).values_list("child_id", "quantity")
            )
            products = dict((p.pk, p) for p in Product.objects.filter(pk__in=product_id_to_quantity.keys()))
            return {products[product_id]: quantity for (product_id, quantity) in six.iteritems(product_id_to_quantity)}
        return {}

    def is_variation_parent(self):
        return self.mode in (ProductMode.SIMPLE_VARIATION_PARENT, ProductMode.VARIABLE_VARIATION_PARENT)

    def is_variation_child(self):
        return (self.mode == ProductMode.VARIATION_CHILD)

    def get_variation_siblings(self):
        return Product.objects.filter(variation_parent=self.variation_parent).exclude(pk=self.pk)

    def is_package_parent(self):
        return (self.mode == ProductMode.PACKAGE_PARENT)

    def is_subscription_parent(self):
        return (self.mode == ProductMode.SUBSCRIPTION)

    def is_package_child(self):
        return ProductPackageLink.objects.filter(child=self).exists()

    def get_all_package_parents(self):
        return Product.objects.filter(pk__in=(
            ProductPackageLink.objects.filter(child=self).values_list("parent", flat=True)
        ))

    def get_all_package_children(self):
        return Product.objects.filter(pk__in=(
            ProductPackageLink.objects.filter(parent=self).values_list("child", flat=True)
        ))

    def get_public_media(self):
        return self.media.filter(enabled=True, public=True).exclude(kind=ProductMediaKind.IMAGE)

    def is_container(self):
        return (self.is_package_parent() or self.is_subscription_parent())


ProductLogEntry = define_log_model(Product)


class ProductCrossSell(models.Model):
    product1 = models.ForeignKey(
        Product, related_name="cross_sell_1", on_delete=models.CASCADE, verbose_name=_("primary product"))
    product2 = models.ForeignKey(
        Product, related_name="cross_sell_2", on_delete=models.CASCADE, verbose_name=_("secondary product"))
    weight = models.IntegerField(default=0, verbose_name=_("weight"))
    type = EnumIntegerField(ProductCrossSellType, verbose_name=_("type"))

    class Meta:
        verbose_name = _('cross sell link')
        verbose_name_plural = _('cross sell links')


class ProductAttribute(AppliedAttribute):
    _applied_fk_field = "product"
    product = models.ForeignKey(Product, related_name='attributes', on_delete=models.CASCADE, verbose_name=_("product"))

    translations = TranslatedFields(
        translated_string_value=models.TextField(blank=True, verbose_name=_("translated value"))
    )

    class Meta:
        abstract = False
        verbose_name = _('product attribute')
        verbose_name_plural = _('product attributes')
