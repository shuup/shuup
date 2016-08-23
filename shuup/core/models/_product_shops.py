# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField

from shuup.core.excs import (
    ProductNotOrderableProblem, ProductNotVisibleProblem
)
from shuup.core.fields import MoneyValueField, QuantityField, UnsavedForeignKey
from shuup.core.signals import get_orderability_errors, get_visibility_errors
from shuup.utils.properties import MoneyPropped, PriceProperty

from ._product_media import ProductMediaKind
from ._products import ProductVisibility, StockBehavior


class ShopProductVisibility(Enum):
    NOT_VISIBLE = 0
    SEARCHABLE = 1
    LISTED = 2
    ALWAYS_VISIBLE = 3

    class Labels:
        NOT_VISIBLE = _("not visible")
        SEARCHABLE = _("searchable")
        LISTED = _("listed")
        ALWAYS_VISIBLE = _("always visible")


class ShopProduct(MoneyPropped, models.Model):
    shop = models.ForeignKey("Shop", related_name="shop_products", on_delete=models.CASCADE, verbose_name=_("shop"))
    product = UnsavedForeignKey(
        "Product", related_name="shop_products", on_delete=models.CASCADE, verbose_name=_("product"))
    suppliers = models.ManyToManyField(
        "Supplier", related_name="shop_products", blank=True, verbose_name=_("suppliers"))

    visibility = EnumIntegerField(
        ShopProductVisibility, default=ShopProductVisibility.NOT_VISIBLE, db_index=True,
        verbose_name=_("visibility")
    )
    purchasable = models.BooleanField(default=True, db_index=True, verbose_name=_("purchasable"))
    visibility_limit = EnumIntegerField(
        ProductVisibility, db_index=True, default=ProductVisibility.VISIBLE_TO_ALL,
        verbose_name=_('visibility limitations')
    )
    visibility_groups = models.ManyToManyField(
        "ContactGroup", related_name='visible_products', verbose_name=_('visible for groups'), blank=True
    )
    backorder_maximum = QuantityField(default=0, blank=True, null=True, verbose_name=_('backorder maximum'))
    purchase_multiple = QuantityField(default=0, verbose_name=_('purchase multiple'))
    minimum_purchase_quantity = QuantityField(default=1, verbose_name=_('minimum purchase'))
    limit_shipping_methods = models.BooleanField(default=False, verbose_name=_("limited for shipping methods"))
    limit_payment_methods = models.BooleanField(default=False, verbose_name=_("limited for payment methods"))
    shipping_methods = models.ManyToManyField(
        "ShippingMethod", related_name='shipping_products', verbose_name=_('shipping methods'), blank=True
    )
    payment_methods = models.ManyToManyField(
        "PaymentMethod", related_name='payment_products', verbose_name=_('payment methods'), blank=True
    )
    primary_category = models.ForeignKey(
        "Category", related_name='primary_shop_products', verbose_name=_('primary category'), blank=True, null=True,
        on_delete=models.PROTECT
    )
    categories = models.ManyToManyField(
        "Category", related_name='shop_products', verbose_name=_('categories'), blank=True
    )
    shop_primary_image = models.ForeignKey(
        "ProductMedia", null=True, blank=True,
        related_name="primary_image_for_shop_products", on_delete=models.SET_NULL,
        verbose_name=_("primary image")
    )

    # the default price of this product in the shop
    default_price = PriceProperty('default_price_value', 'shop.currency', 'shop.prices_include_tax')
    default_price_value = MoneyValueField(verbose_name=_("default price"), null=True, blank=True)

    minimum_price = PriceProperty('minimum_price_value', 'shop.currency', 'shop.prices_include_tax')
    minimum_price_value = MoneyValueField(verbose_name=_("minimum price"), null=True, blank=True)

    class Meta:
        unique_together = (("shop", "product",),)

    def save(self, *args, **kwargs):
        super(ShopProduct, self).save(*args, **kwargs)
        for supplier in self.suppliers.all():
            supplier.module.update_stock(product_id=self.product.id)

    def is_list_visible(self):
        """
        Return True if this product should be visible in listings in general,
        without taking into account any other visibility limitations.
        :rtype: bool
        """
        if self.product.deleted:
            return False
        if not self.listed:
            return False
        if self.product.is_variation_child():
            return False
        return True

    @property
    def primary_image(self):
        if self.shop_primary_image_id:
            return self.shop_primary_image
        else:
            return self.product.primary_image

    @property
    def searchable(self):
        return self.visibility in (ShopProductVisibility.SEARCHABLE, ShopProductVisibility.ALWAYS_VISIBLE)

    @property
    def listed(self):
        return self.visibility in (ShopProductVisibility.LISTED, ShopProductVisibility.ALWAYS_VISIBLE)

    @property
    def visible(self):
        return not (self.visibility == ShopProductVisibility.NOT_VISIBLE)

    @property
    def public_primary_image(self):
        primary_image = self.primary_image
        return primary_image if primary_image and primary_image.public else None

    def get_visibility_errors(self, customer):
        if self.product.deleted:
            yield ValidationError(_('This product has been deleted.'), code="product_deleted")

        if customer and customer.is_all_seeing:  # None of the further conditions matter for omniscient customers.
            return

        if not self.visible:
            yield ValidationError(_('This product is not visible.'), code="product_not_visible")

        is_logged_in = (bool(customer) and not customer.is_anonymous)

        if not is_logged_in and self.visibility_limit != ProductVisibility.VISIBLE_TO_ALL:
            yield ValidationError(
                _('The Product is invisible to users not logged in.'),
                code="product_not_visible_to_anonymous")

        if is_logged_in and self.visibility_limit == ProductVisibility.VISIBLE_TO_GROUPS:
            # TODO: Optimization
            user_groups = set(customer.groups.all().values_list("pk", flat=True))
            my_groups = set(self.visibility_groups.values_list("pk", flat=True))
            if not bool(user_groups & my_groups):
                yield ValidationError(
                    _('This product is not visible to your group.'),
                    code="product_not_visible_to_group"
                )

        for receiver, response in get_visibility_errors.send(ShopProduct, shop_product=self, customer=customer):
            for error in response:
                yield error

    # TODO: Refactor get_orderability_errors, it's too complex
    def get_orderability_errors(  # noqa (C901)
            self, supplier, quantity, customer, ignore_minimum=False):
        """
        Yield ValidationErrors that would cause this product to not be orderable.

        :param supplier: Supplier to order this product from. May be None.
        :type supplier: shuup.core.models.Supplier
        :param quantity: Quantity to order.
        :type quantity: int|Decimal
        :param customer: Customer contact.
        :type customer: shuup.core.models.Contact
        :param ignore_minimum: Ignore any limitations caused by quantity minimums.
        :type ignore_minimum: bool
        :return: Iterable[ValidationError]
        """
        for error in self.get_visibility_errors(customer):
            yield error

        if supplier is None and not self.suppliers.exists():
            # `ShopProduct` must have at least one `Supplier`.
            # If supplier is not given and the `ShopProduct` itself
            # doesn't have suppliers we cannot sell this product.
            yield ValidationError(
                _('The product has no supplier.'),
                code="no_supplier"
            )

        if not ignore_minimum and quantity < self.minimum_purchase_quantity:
            yield ValidationError(
                _('The purchase quantity needs to be at least %d for this product.') % self.minimum_purchase_quantity,
                code="purchase_quantity_not_met"
            )

        if supplier and not self.suppliers.filter(pk=supplier.pk).exists():
            yield ValidationError(
                _('The product is not supplied by %s.') % supplier,
                code="invalid_supplier"
            )

        if self.product.is_package_parent():
            for child_product, child_quantity in six.iteritems(self.product.get_package_child_to_quantity_map()):
                child_shop_product = child_product.get_shop_instance(shop=self.shop)
                if not child_shop_product:
                    yield ValidationError("%s: Not available in %s" % (child_product, self.shop), code="invalid_shop")
                for error in child_shop_product.get_orderability_errors(
                        supplier=supplier,
                        quantity=(quantity * child_quantity),
                        customer=customer,
                        ignore_minimum=ignore_minimum
                ):
                    code = getattr(error, "code", None)
                    yield ValidationError("%s: %s" % (child_product, error), code=code)

        if supplier and self.product.stock_behavior == StockBehavior.STOCKED:
            for error in supplier.get_orderability_errors(self, quantity, customer=customer):
                yield error

        purchase_multiple = self.purchase_multiple
        if quantity > 0 and purchase_multiple > 1 and (quantity % purchase_multiple) != 0:
            p = (quantity // purchase_multiple)
            smaller_p = max(purchase_multiple, p * purchase_multiple)
            larger_p = max(purchase_multiple, (p + 1) * purchase_multiple)
            if larger_p == smaller_p:
                message = _('The product can only be ordered in multiples of %(package_size)s, '
                            'for example %(smaller_p)s %(unit)s.') % {
                    "package_size": purchase_multiple,
                    "smaller_p": smaller_p,
                    "unit": self.product.sales_unit,
                }
            else:
                message = _('The product can only be ordered in multiples of %(package_size)s, '
                            'for example %(smaller_p)s or %(larger_p)s %(unit)s.') % {
                    "package_size": purchase_multiple,
                    "smaller_p": smaller_p,
                    "larger_p": larger_p,
                    "unit": self.product.sales_unit,
                }
            yield ValidationError(message, code="invalid_purchase_multiple")

        for receiver, response in get_orderability_errors.send(
            ShopProduct, shop_product=self, customer=customer, supplier=supplier, quantity=quantity
        ):
            for error in response:
                yield error

    def raise_if_not_orderable(self, supplier, customer, quantity, ignore_minimum=False):
        for message in self.get_orderability_errors(
            supplier=supplier, quantity=quantity, customer=customer, ignore_minimum=ignore_minimum
        ):
            raise ProductNotOrderableProblem(message.args[0])

    def raise_if_not_visible(self, customer):
        for message in self.get_visibility_errors(customer=customer):
            raise ProductNotVisibleProblem(message.args[0])

    def is_orderable(self, supplier, customer, quantity):
        if not supplier:
            supplier = self.suppliers.first()  # TODO: Allow multiple suppliers
        for message in self.get_orderability_errors(supplier=supplier, quantity=quantity, customer=customer):
            return False
        return True

    def is_visible(self, customer):
        for message in self.get_visibility_errors(customer=customer):
            return False
        return True

    @property
    def quantity_step(self):
        """
        Quantity step for purchasing this product.

        :rtype: decimal.Decimal

        Example:
            <input type="number" step="{{ shop_product.quantity_step }}">
        """
        if self.purchase_multiple:
            return self.purchase_multiple
        return self.product.sales_unit.quantity_step

    @property
    def rounded_minimum_purchase_quantity(self):
        """
        The minimum purchase quantity, rounded to the sales unit's precision.

        :rtype: decimal.Decimal

        Example:
            <input type="number"
                min="{{ shop_product.rounded_minimum_purchase_quantity }}"
                value="{{ shop_product.rounded_minimum_purchase_quantity }}">

        """
        return self.product.sales_unit.round(self.minimum_purchase_quantity)

    @property
    def images(self):
        return self.product.media.filter(shops=self.shop, kind=ProductMediaKind.IMAGE).order_by("ordering")

    @property
    def public_images(self):
        return self.images.filter(public=True)
