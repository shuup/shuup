# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import six
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.excs import ImpossibleProductModeException
from shoop.core.fields import InternalIdentifierField, MeasurementField
from shoop.core.taxing import TaxableItem
from shoop.core.utils.slugs import generate_multilanguage_slugs
from shoop.utils.analog import define_log_model, LogEntryKind

from ._attributes import AppliedAttribute, AttributableMixin, Attribute
from ._product_packages import ProductPackageLink
from ._product_variation import (
    get_all_available_combinations, get_combination_hash_from_variable_mapping,
    ProductVariationResult, ProductVariationVariable
)


class ProductMode(Enum):
    NORMAL = 0
    PACKAGE_PARENT = 1
    SIMPLE_VARIATION_PARENT = 2
    VARIABLE_VARIATION_PARENT = 3
    VARIATION_CHILD = 4

    class Labels:
        NORMAL = _('normal')
        PACKAGE_PARENT = _('package parent')
        SIMPLE_VARIATION_PARENT = _('variation parent (simple)')
        VARIABLE_VARIATION_PARENT = _('variation parent (variable)')
        VARIATION_CHILD = _('variation child')


class ProductVisibility(Enum):
    VISIBLE_TO_ALL = 1
    VISIBLE_TO_LOGGED_IN = 2
    VISIBLE_TO_GROUPS = 3

    class Labels:
        VISIBLE_TO_ALL = _('visible to all')
        VISIBLE_TO_LOGGED_IN = _('visible to logged in')
        VISIBLE_TO_GROUPS = _('visible to groups')


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

    class Labels:
        RECOMMENDED = _('recommended')
        RELATED = _('related')
        COMPUTED = _('computed')


class ShippingMode(Enum):
    NOT_SHIPPED = 0
    SHIPPED = 1

    class Labels:
        NOT_SHIPPED = _('not shipped')
        SHIPPED = _('shipped')


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
        name=models.CharField(max_length=64, verbose_name=_('name')),
    )
    attributes = models.ManyToManyField(
        "Attribute", blank=True, related_name='product_types',
        verbose_name=_('attributes'))

    class Meta:
        verbose_name = _('product type')
        verbose_name_plural = _('product types')

    def __str__(self):
        return (self.safe_translation_getter("name") or self.identifier)


class ProductQuerySet(TranslatableQuerySet):
    def list_visible(self, shop, customer, language=None):
        root = (self.language(language) if language else self)

        if customer and customer.is_all_seeing:
            exclude_q = Q(deleted=True) | Q(mode=ProductMode.VARIATION_CHILD)
            qs = root.all().exclude(exclude_q).filter(shop_products__shop=shop)
        else:
            qs = root.all().exclude(deleted=True).filter(
                shop_products__shop=shop,
                shop_products__visible=True,
                shop_products__listed=True,
                mode__in=(
                    ProductMode.NORMAL, ProductMode.PACKAGE_PARENT,
                    ProductMode.SIMPLE_VARIATION_PARENT, ProductMode.VARIABLE_VARIATION_PARENT
                )
            )
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

        qs = qs.select_related(*Product.COMMON_SELECT_RELATED)
        return qs

    def all_except_deleted(self, language=None):
        qs = (self.language(language) if language else self).exclude(deleted=True)
        qs = qs.select_related(*Product.COMMON_SELECT_RELATED)
        return qs


@python_2_unicode_compatible
class Product(TaxableItem, AttributableMixin, TranslatableModel):
    COMMON_SELECT_RELATED = ("type", "primary_image", "tax_class")

    # Metadata
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('modified on'))
    deleted = models.BooleanField(default=False, editable=False, db_index=True, verbose_name=_('deleted'))

    # Behavior
    mode = EnumIntegerField(ProductMode, default=ProductMode.NORMAL, verbose_name=_('mode'))
    variation_parent = models.ForeignKey(
        "self", null=True, blank=True, related_name='variation_children',
        on_delete=models.PROTECT,
        verbose_name=_('variation parent'))
    stock_behavior = EnumIntegerField(StockBehavior, default=StockBehavior.UNSTOCKED, verbose_name=_('stock'))
    shipping_mode = EnumIntegerField(ShippingMode, default=ShippingMode.NOT_SHIPPED, verbose_name=_('shipping mode'))
    sales_unit = models.ForeignKey("SalesUnit", verbose_name=_('unit'), blank=True, null=True, on_delete=models.PROTECT)
    tax_class = models.ForeignKey("TaxClass", verbose_name=_('tax class'), on_delete=models.PROTECT)

    # Identification
    type = models.ForeignKey(
        "ProductType", related_name='products',
        on_delete=models.PROTECT, db_index=True,
        verbose_name=_('product type'))
    sku = models.CharField(db_index=True, max_length=128, verbose_name=_('SKU'), unique=True)
    gtin = models.CharField(blank=True, max_length=40, verbose_name=_('GTIN'), help_text=_('Global Trade Item Number'))
    barcode = models.CharField(blank=True, max_length=40, verbose_name=_('barcode'))
    accounting_identifier = models.CharField(max_length=32, blank=True, verbose_name=_('bookkeeping account'))
    profit_center = models.CharField(max_length=32, verbose_name=_('profit center'), blank=True)
    cost_center = models.CharField(max_length=32, verbose_name=_('cost center'), blank=True)
    # Category is duplicated here because not all products necessarily belong in Shops (i.e. have
    # ShopProduct instances), but they should nevertheless be searchable by category in other
    # places, such as administration UIs.
    category = models.ForeignKey(
        "Category", related_name='primary_products', blank=True, null=True,
        verbose_name=_('primary category'),
        help_text=_("only used for administration and reporting"), on_delete=models.PROTECT)

    # Physical dimensions
    width = MeasurementField(unit="mm", verbose_name=_('width (mm)'))
    height = MeasurementField(unit="mm", verbose_name=_('height (mm)'))
    depth = MeasurementField(unit="mm", verbose_name=_('depth (mm)'))
    net_weight = MeasurementField(unit="g", verbose_name=_('net weight (g)'))
    gross_weight = MeasurementField(unit="g", verbose_name=_('gross weight (g)'))

    # Misc.
    manufacturer = models.ForeignKey(
        "Manufacturer", blank=True, null=True,
        verbose_name=_('manufacturer'), on_delete=models.PROTECT)
    primary_image = models.ForeignKey(
        "ProductMedia", null=True, blank=True,
        related_name="primary_image_for_products",
        on_delete=models.SET_NULL,
        verbose_name=_("primary image"))

    translations = TranslatedFields(
        name=models.CharField(max_length=256, verbose_name=_('name')),
        description=models.TextField(blank=True, verbose_name=_('description')),
        slug=models.SlugField(verbose_name=_('slug'), max_length=255, null=True),
        keywords=models.TextField(blank=True, verbose_name=_('keywords')),
        status_text=models.CharField(
            max_length=128, blank=True,
            verbose_name=_('status text'),
            help_text=_(
                'This text will be shown alongside the product in the shop.'
                ' (Ex.: "Available in a month")')),
        variation_name=models.CharField(
            max_length=128, blank=True,
            verbose_name=_('variation name'))
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

    def get_shop_instance(self, shop):
        """
        :type shop: shoop.core.models.Shop
        :rtype: shoop.core.models.ShopProduct
        """
        shop_inst_cache = self.__dict__.setdefault("_shop_inst_cache", {})
        cached = shop_inst_cache.get(shop)
        if cached:
            return cached

        shop_inst = self.shop_products.get(shop=shop)
        shop_inst._product_cache = self
        shop_inst._shop_cache = shop
        shop_inst_cache[shop] = shop_inst

        return shop_inst

    def get_cheapest_child_price(self, context, quantity=1):
        price_info = self.get_cheapest_child_price_info(context, quantity)
        if price_info:
            return price_info.price

    def get_child_price_range(self, context, quantity=1):
        """
        Get the prices for cheapest and the most expensive child

        The attribute used for sorting is `PriceInfo.price`.

        Return (`None`, `None`) if `self.variation_children` do not exist.
        This is because we cannot return anything sensible.

        :type context: shoop.core.pricing.PricingContextable
        :type quantity: int
        :return: a tuple of prices
        :rtype: (shoop.core.pricing.Price, shoop.core.pricing.Price)
        """
        items = [c.get_price_info(context, quantity=quantity) for c in self.variation_children.all()]
        if not items:
            return (None, None)

        infos = sorted(items, key=lambda x: x.price)
        return (infos[0].price, infos[-1].price)

    def get_cheapest_child_price_info(self, context, quantity=1):
        """
        Get the `PriceInfo` of the cheapest variation child

        The attribute used for sorting is `PriceInfo.price`.

        Return `None` if `self.variation_children` do not exist.
        This is because we cannot return anything sensible.

        :type context: shoop.core.pricing.PricingContextable
        :rtype: shoop.core.pricing.PriceInfo
        """
        items = [c.get_price_info(context, quantity=quantity) for c in self.variation_children.all()]
        if not items:
            return None

        return sorted(items, key=lambda x: x.price)[0]

    def get_price_info(self, context, quantity=1):
        """
        Get `PriceInfo` object for the product in given context.

        Returned `PriceInfo` object contains calculated `price` and
        `base_price`.  The calculation of prices is handled in the
        current pricing module.

        :type context: shoop.core.pricing.PricingContextable
        :rtype: shoop.core.pricing.PriceInfo
        """
        from shoop.core.pricing import get_pricing_module
        module = get_pricing_module()
        pricing_context = module.get_context(context)
        return module.get_price_info(pricing_context, product=self, quantity=quantity)

    def get_price(self, context, quantity=1):
        """
        Get price of the product within given context.

        .. note::

           When the current pricing module implements pricing steps, it
           is possible that ``p.get_price(ctx) * 123`` is not equal to
           ``p.get_price(ctx, quantity=123)``, since there could be
           quantity discounts in effect, but usually they are equal.

        :type context: shoop.core.pricing.PricingContextable
        :rtype: shoop.core.pricing.Price
        """
        return self.get_price_info(context, quantity).price

    def get_base_price(self, context, quantity=1):
        """
        Get base price of the product within given context.

        Base price differs from the (effective) price when there are
        discounts in effect.

        :type context: shoop.core.pricing.PricingContextable
        :rtype: shoop.core.pricing.Price
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

        :return: Mapping of combination hashes to product IDs
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
        (For example 6 variables with 5 options each explodes to 15,625 combinations.)

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
        Remove variation variables from the given variation parent, turning it
        into a simple variation (or a normal product, if it has no children).

        :param product: Variation parent to not be variable any longer.
        :type product: shoop.core.models.Product
        """
        ProductVariationVariable.objects.filter(product=self).delete()
        ProductVariationResult.objects.filter(product=self).delete()
        self.verify_mode()
        self.save()

    @staticmethod
    def _get_slug_name(self):
        if self.deleted:
            return None
        return (self.safe_translation_getter("name") or self.sku)

    def save(self, *args, **kwargs):
        if self.net_weight and self.net_weight > 0:
            self.gross_weight = max(self.net_weight, self.gross_weight)
        rv = super(Product, self).save(*args, **kwargs)
        generate_multilanguage_slugs(self, self._get_slug_name)
        return rv

    def delete(self, using=None):
        raise NotImplementedError("Not implemented: Use `soft_delete()` for products.")

    def soft_delete(self, user=None):
        if not self.deleted:
            self.deleted = True
            self.add_log_entry("Deleted.", kind=LogEntryKind.DELETION, user=user)
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
        :param variables: Optional dict of {variable identifier: value identifier} for complex variable linkage
        :type variables: dict|None
        :param combination_hash: Optional combination hash (for variable variations), if precomputed. Mutually
                                 exclusive with `variables`
        :type combination_hash: str|None

        """
        if combination_hash:
            if variables:
                raise ValueError("`combination_hash` and `variables` are mutually exclusive")
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
        Validates relation possibility for `self.link_to_parent()`

        :param parent: parent product of self
        :type parent: Product
        :param variables:
        :type variables: dict|None
        """
        if parent.is_variation_child():
            raise ImpossibleProductModeException(
                _("Multilevel parentage hierarchies aren't supported (parent is a child already)"),
                code="multilevel"
            )
        if parent.mode == ProductMode.VARIABLE_VARIATION_PARENT and not variables:
            raise ImpossibleProductModeException(
                _("Parent is a variable variation parent, yet variables were not passed"),
                code="no_variables"
            )
        if parent.mode == ProductMode.SIMPLE_VARIATION_PARENT and variables:
            raise ImpossibleProductModeException(
                "Parent is a simple variation parent, yet variables were passed",
                code="extra_variables"
            )
        if self.mode == ProductMode.SIMPLE_VARIATION_PARENT:
            raise ImpossibleProductModeException(
                _("Multilevel parentage hierarchies aren't supported (this product is a simple variation parent)"),
                code="multilevel"
            )
        if self.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            raise ImpossibleProductModeException(
                _("Multilevel parentage hierarchies aren't supported (this product is a variable variation parent)"),
                code="multilevel"
            )

    def make_package(self, package_def):
        if self.mode != ProductMode.NORMAL:
            raise ImpossibleProductModeException(
                _("Product is currently not a normal product, can't turn into package"),
                code="abnormal"
            )

        for child_product, quantity in six.iteritems(package_def):
            # :type child_product: Product
            if child_product.is_variation_parent():
                raise ImpossibleProductModeException(
                    _("Variation parents can not belong into a package"),
                    code="abnormal"
                )
            if child_product.is_package_parent():
                raise ImpossibleProductModeException(_("Packages can't be nested"), code="multilevel")
            if quantity <= 0:
                raise ImpossibleProductModeException(_("Quantity %s is invalid") % quantity, code="quantity")
            ProductPackageLink.objects.create(parent=self, child=child_product, quantity=quantity)
        self.verify_mode()

    def get_package_child_to_quantity_map(self):
        if self.is_package_parent():
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
        return self.media.filter(enabled=True, public=True)


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
