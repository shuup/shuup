# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import warnings

import six
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.excs import (
    ProductNotOrderableProblem, ProductNotVisibleProblem
)
from shuup.core.fields import MoneyValueField, QuantityField, UnsavedForeignKey
from shuup.core.signals import (
    get_orderability_errors, get_visibility_errors, post_clean, pre_clean
)
from shuup.core.utils import context_cache
from shuup.utils.analog import define_log_model
from shuup.utils.importing import cached_load
from shuup.utils.properties import MoneyPropped, PriceProperty

from ._product_media import ProductMediaKind
from ._products import ProductMode, ProductVisibility
from ._units import DisplayUnit, PiecesSalesUnit, UnitInterface

mark_safe_lazy = lazy(mark_safe, six.text_type)


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


class ShopProduct(MoneyPropped, TranslatableModel):
    shop = models.ForeignKey("Shop", related_name="shop_products", on_delete=models.CASCADE, verbose_name=_("shop"))
    product = UnsavedForeignKey(
        "Product", related_name="shop_products", on_delete=models.CASCADE, verbose_name=_("product"))
    suppliers = models.ManyToManyField(
        "Supplier", related_name="shop_products", blank=True, verbose_name=_("suppliers"), help_text=_(
            "List your suppliers here. Suppliers can be found by searching for `Suppliers`."
        )
    )

    visibility = EnumIntegerField(
        ShopProductVisibility,
        default=ShopProductVisibility.ALWAYS_VISIBLE,
        db_index=True,
        verbose_name=_("visibility"),
        help_text=mark_safe_lazy(_(
            "Choose how you want your product to be seen and found by the customers. "
            "<p>Not visible: Product will not be shown in your store front nor found in search.</p>"
            "<p>Searchable: Product will be shown in search, but not listed on any category page.</p>"
            "<p>Listed: Product will be shown on category pages, but not shown in search results.</p>"
            "<p>Always Visible: Product will be shown in your store front and found in search.</p>"
        ))
    )
    purchasable = models.BooleanField(default=True, db_index=True, verbose_name=_("purchasable"))
    visibility_limit = EnumIntegerField(
        ProductVisibility, db_index=True, default=ProductVisibility.VISIBLE_TO_ALL,
        verbose_name=_('visibility limitations'), help_text=_(
            "Select whether you want your product to have special limitations on its visibility in your store. "
            "You can make products visible to all, visible to only logged-in users, or visible only to certain "
            "customer groups."
        )
    )
    visibility_groups = models.ManyToManyField(
        "ContactGroup", related_name='visible_products', verbose_name=_('visible for groups'), blank=True, help_text=_(
            u"Select the groups you want to make your product visible for. "
            u"These groups are defined in Contacts Settings - Contact Groups."
        )
    )
    backorder_maximum = QuantityField(
        default=0, blank=True, null=True, verbose_name=_('backorder maximum'), help_text=_(
            "The number of units that can be purchased after the product is already sold out (out of stock). "
            "Set to blank for product to be purchasable without limits."
        ))
    purchase_multiple = QuantityField(default=0, verbose_name=_('purchase multiple'), help_text=_(
            "Set this to other than 0 if the product needs to be purchased in multiples. "
            "For example, if the purchase multiple is set to 2, then customers are required to order the product "
            "in multiples of 2. Not to be confused with the Minimum Purchase Quantity."
        )
    )
    minimum_purchase_quantity = QuantityField(default=1, verbose_name=_('minimum purchase quantity'), help_text=_(
            "Set a minimum number of products needed to be ordered for the purchase. "
            "This is useful for setting bulk orders and B2B purchases."
        )
    )
    limit_shipping_methods = models.BooleanField(
        default=False, verbose_name=_("limit the shipping methods"), help_text=_(
            "Enable this if you want to limit your product to use only the select shipping methods. "
            "You can select the allowed shipping method(s) in the field below - all the rest "
            "are disallowed."
        )
    )
    limit_payment_methods = models.BooleanField(
        default=False, verbose_name=_("limit the payment methods"), help_text=_(
            "Enable this if you want to limit your product to use only the select payment methods. "
            "You can select the allowed payment method(s) in the field below - all the rest "
            "are disallowed."
        )
    )
    shipping_methods = models.ManyToManyField(
        "ShippingMethod", related_name='shipping_products', verbose_name=_('shipping methods'), blank=True, help_text=_(
            "If you enabled the `Limit the payment methods` choice above, then here you can select the "
            "individual shipping methods you want to ALLOW for this product. The ones not mentioned are "
            "disabled. To change this, search for `Shipping Methods`."
        )
    )
    payment_methods = models.ManyToManyField(
        "PaymentMethod", related_name='payment_products', verbose_name=_('payment methods'), blank=True, help_text=_(
            "If you enabled the `Limit the payment methods` choice above, then here you can select the "
            "individuals payment methods you want to ALLOW for this product. The ones not mentioned are "
            "disabled. To change this, search for `Payment Methods`."
        )
    )
    primary_category = models.ForeignKey(
        "Category", related_name='primary_shop_products', verbose_name=_('primary category'), blank=True, null=True,
        on_delete=models.PROTECT, help_text=_(
            "Choose the primary category for the product. "
            "This will be the main category for classification in the system. "
            "The product will be found under this category in your store. "
            "To change this, search for `Categories`."
        )
    )
    categories = models.ManyToManyField(
        "Category", related_name='shop_products', verbose_name=_('categories'), blank=True, help_text=_(
            "Add secondary categories for your product. "
            "These are other categories that your product fits under and that it can be found by in your store."
        )
    )
    shop_primary_image = models.ForeignKey(
        "ProductMedia", null=True, blank=True,
        related_name="primary_image_for_shop_products", on_delete=models.SET_NULL,
        verbose_name=_("primary image"), help_text=_(
            "Click this to set this image as the primary display image for the product."
        )
    )

    # the default price of this product in the shop
    default_price = PriceProperty('default_price_value', 'shop.currency', 'shop.prices_include_tax')
    default_price_value = MoneyValueField(verbose_name=_("default price"), null=True, blank=True, help_text=_(
            "This is the default individual base unit (or multi-pack) price of the product. "
            "All discounts or coupons will be calculated based off of this price."
        )
    )

    minimum_price = PriceProperty('minimum_price_value', 'shop.currency', 'shop.prices_include_tax')
    minimum_price_value = MoneyValueField(verbose_name=_("minimum price"), null=True, blank=True, help_text=_(
            "This is the default price that the product cannot go under in your store, "
            "despite coupons or discounts being applied. "
            "This is useful to make sure your product price stays above the cost."
        )
    )
    available_until = models.DateTimeField(verbose_name=_("available until"), null=True, blank=True, help_text=_(
        "After this date this product will be invisible in store front."
    ))

    display_unit = models.ForeignKey(
        DisplayUnit,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_("display unit"),
        help_text=_("Unit for displaying quantities of this product.")
    )

    translations = TranslatedFields(
        name=models.CharField(
            blank=True, null=True, max_length=256, verbose_name=_('name'),
            help_text=_("Enter a descriptive name for your product. This will be its title in your store front.")),
        description=models.TextField(
            blank=True, null=True, verbose_name=_('description'),
            help_text=_(
                "To make your product stands out, give it an awesome description. "
                "This is what will help your shoppers learn about your products. "
                "It will also help shoppers find them in the store and on the web."
            )
        ),
        short_description=models.CharField(
            blank=True, null=True, max_length=150, verbose_name=_('short description'),
            help_text=_(
                "Enter a short description for your product. The short description will "
                "be used to get the attention of your customer with a small, but "
                "precise description of your product. It also helps with getting more "
                "traffic via search engines."
            )
        ),
        status_text=models.CharField(
            max_length=128, blank=True,
            verbose_name=_('status text'),
            help_text=_(
                'This text will be shown alongside the product in the shop. '
                'It is useful for informing customers of special stock numbers or preorders. '
                '(Ex.: Available in a month)'
            )
        )
    )

    class Meta:
        unique_together = (("shop", "product",),)
        verbose_name = _("shop product")
        verbose_name_plural = _("shop products")

    def save(self, *args, **kwargs):
        self.clean()
        super(ShopProduct, self).save(*args, **kwargs)
        for supplier in self.suppliers.enabled():
            supplier.module.update_stock(product_id=self.product.id)

    def clean(self):
        pre_clean.send(type(self), instance=self)
        super(ShopProduct, self).clean()
        if self.display_unit:
            if self.display_unit.internal_unit != self.product.sales_unit:
                raise ValidationError({'display_unit': _(
                    "Error! Invalid display unit: Internal unit of "
                    "the selected display unit does not match "
                    "with the sales unit of the product.")})
        post_clean.send(type(self), instance=self)

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
            yield ValidationError(_("This product has been deleted."), code="product_deleted")

        if customer and customer.is_all_seeing:  # None of the further conditions matter for omniscient customers.
            return

        if not self.visible:
            yield ValidationError(_("This product is not visible."), code="product_not_visible")

        if self.available_until and self.available_until <= now():
            yield ValidationError(
                _("Error! This product is not available until the current date."),
                code="product_not_available"
            )

        is_logged_in = (bool(customer) and not customer.is_anonymous)

        if not is_logged_in and self.visibility_limit != ProductVisibility.VISIBLE_TO_ALL:
            yield ValidationError(
                _("The Product is invisible to users not logged in."),
                code="product_not_visible_to_anonymous")

        if is_logged_in and self.visibility_limit == ProductVisibility.VISIBLE_TO_GROUPS:
            # TODO: Optimization
            user_groups = set(customer.groups.all().values_list("pk", flat=True))
            my_groups = set(self.visibility_groups.values_list("pk", flat=True))
            if not bool(user_groups & my_groups):
                yield ValidationError(
                    _("This product is not visible to your group."),
                    code="product_not_visible_to_group"
                )

        # TODO: Remove from Shuup 2.0
        for receiver, response in get_visibility_errors.send(ShopProduct, shop_product=self, customer=customer):
            warnings.warn("Warning! Visibility errors through signals are deprecated.", DeprecationWarning)
            for error in response:
                yield error

    def get_orderability_errors(self, supplier, quantity, customer, ignore_minimum=False):
        """
        Yield ValidationErrors that would cause this product to not be orderable.

        Shop product to be orderable it needs to be visible visible and purchasable.

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

        for error in self.get_purchasability_errors(supplier, customer, quantity, ignore_minimum):
            yield error

    def get_purchasability_errors(self, supplier, customer, quantity, ignore_minimum=False):
        """
        Yield ValidationErrors that would cause this product to not be purchasable.

        Shop product to be purchasable it has to have purchasable attribute set on
        and pass all quantity and supplier checks.

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
        if not self.purchasable:
            yield ValidationError(_("The product is not purchasable."), code="not_purchasable")

        for error in self.get_quantity_errors(quantity, ignore_minimum):
            yield error

        for error in self.get_supplier_errors(supplier, customer, quantity, ignore_minimum):
            yield error

        # TODO: Remove from Shuup 2.0
        for receiver, response in get_orderability_errors.send(
            ShopProduct, shop_product=self, customer=customer, supplier=supplier, quantity=quantity
        ):
            warnings.warn("Warning! Orderability errors through signals are deprecated.", DeprecationWarning)
            for error in response:
                yield error

    def get_quantity_errors(self, quantity, ignore_minimum):
        if not ignore_minimum and quantity < self.minimum_purchase_quantity:
            yield ValidationError(
                _("The purchase quantity needs to be at least %d for this product.")
                % self.minimum_purchase_quantity,
                code="purchase_quantity_not_met"
            )

        purchase_multiple = self.purchase_multiple
        if quantity > 0 and purchase_multiple > 0 and (quantity % purchase_multiple) != 0:
            p = (quantity // purchase_multiple)
            smaller_p = max(purchase_multiple, p * purchase_multiple)
            larger_p = max(purchase_multiple, (p + 1) * purchase_multiple)
            render_qty = self.unit.render_quantity
            if larger_p == smaller_p:
                message = _(
                    "The product can only be ordered in multiples of "
                    "{package_size}, for example {amount}.").format(
                        package_size=render_qty(purchase_multiple),
                        amount=render_qty(smaller_p))
            else:
                message = _(
                    "The product can only be ordered in multiples of "
                    "{package_size}, for example {smaller_amount} or "
                    "{larger_amount}.").format(
                        package_size=render_qty(purchase_multiple),
                        smaller_amount=render_qty(smaller_p),
                        larger_amount=render_qty(larger_p))
            yield ValidationError(message, code="invalid_purchase_multiple")

    def get_supplier_errors(self, supplier, customer, quantity, ignore_minimum):
        enabled_supplier = self.suppliers.enabled(shop=self.shop)
        if supplier is None and not enabled_supplier.exists():
            # `ShopProduct` must have at least one `Supplier`.
            # If supplier is not given and the `ShopProduct` itself
            # doesn't have suppliers we cannot sell this product.
            yield ValidationError(
                _("The product has no supplier."),
                code="no_supplier"
            )

        if supplier and not enabled_supplier.filter(pk=supplier.pk).exists():
            yield ValidationError(
                _("The product is not supplied by %s.") % supplier,
                code="invalid_supplier"
            )

        errors = []
        if self.product.mode == ProductMode.SIMPLE_VARIATION_PARENT:
            errors = self.get_orderability_errors_for_simple_variation_parent(supplier, customer)
        elif self.product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            errors = self.get_orderability_errors_for_variable_variation_parent(supplier, customer)
        elif self.product.is_package_parent():
            errors = self.get_orderability_errors_for_package_parent(supplier, customer, quantity, ignore_minimum)
        elif supplier:  # Test supplier orderability only for variation children and normal products
            errors = supplier.get_orderability_errors(self, quantity, customer=customer)

        for error in errors:
            yield error

    def get_orderability_errors_for_simple_variation_parent(self, supplier, customer):
        sellable = False
        for child_product in self.product.variation_children.visible(shop=self.shop, customer=customer):
            try:
                child_shop_product = child_product.get_shop_instance(self.shop)
            except ShopProduct.DoesNotExist:
                continue

            if child_shop_product.is_orderable(
                    supplier=supplier,
                    customer=customer,
                    quantity=child_shop_product.minimum_purchase_quantity,
                    allow_cache=False
            ):
                sellable = True
                break

        if not sellable:
            yield ValidationError(_("Product has no sellable children."), code="no_sellable_children")

    def get_orderability_errors_for_variable_variation_parent(self, supplier, customer):
        from shuup.core.models import ProductVariationResult
        sellable = False
        for combo in self.product.get_all_available_combinations():
            res = ProductVariationResult.resolve(self.product, combo["variable_to_value"])
            if not res:
                continue
            try:
                child_shop_product = res.get_shop_instance(self.shop)
            except ShopProduct.DoesNotExist:
                continue

            if child_shop_product.is_orderable(
                    supplier=supplier,
                    customer=customer,
                    quantity=child_shop_product.minimum_purchase_quantity,
                    allow_cache=False
            ):
                sellable = True
                break
        if not sellable:
            yield ValidationError(_("Product has no sellable children."), code="no_sellable_children")

    def get_orderability_errors_for_package_parent(self, supplier, customer, quantity, ignore_minimum):
        for child_product, child_quantity in six.iteritems(self.product.get_package_child_to_quantity_map()):
            try:
                child_shop_product = child_product.get_shop_instance(shop=self.shop, allow_cache=False)
            except ShopProduct.DoesNotExist:
                yield ValidationError(
                    "Error! %s is not available in %s." % (child_product, self.shop), code="invalid_shop")
            else:
                for error in child_shop_product.get_orderability_errors(
                        supplier=supplier,
                        quantity=(quantity * child_quantity),
                        customer=customer,
                        ignore_minimum=ignore_minimum
                ):
                    message = getattr(error, "message", "")
                    code = getattr(error, "code", None)
                    yield ValidationError("Error! %s: %s" % (child_product, message), code=code)

    def raise_if_not_orderable(self, supplier, customer, quantity, ignore_minimum=False):
        for message in self.get_orderability_errors(
            supplier=supplier, quantity=quantity, customer=customer, ignore_minimum=ignore_minimum
        ):
            raise ProductNotOrderableProblem(message.args[0])

    def raise_if_not_visible(self, customer):
        for message in self.get_visibility_errors(customer=customer):
            raise ProductNotVisibleProblem(message.args[0])

    def is_orderable(self, supplier, customer, quantity, allow_cache=True):
        """
        Product to be orderable it needs to be visible and purchasable.
        """
        key, val = context_cache.get_cached_value(
            identifier="is_orderable", item=self, context={"customer": customer},
            supplier=supplier, stock_managed=bool(supplier and supplier.stock_managed),
            quantity=quantity, allow_cache=allow_cache)
        if customer and val is not None:
            return val

        if not supplier:
            supplier = self.get_supplier(customer, quantity)

        for message in self.get_orderability_errors(supplier=supplier, quantity=quantity, customer=customer):
            if customer:
                context_cache.set_cached_value(key, False)
            return False

        if customer:
            context_cache.set_cached_value(key, True)
        return True

    def is_visible(self, customer):
        """
        Visible products are shown in store front based on customer
        or customer group limitations.
        """
        for message in self.get_visibility_errors(customer=customer):
            return False
        return True

    def is_purchasable(self, supplier, customer, quantity):
        """
        Whether product can be purchased.
        """
        for message in self.get_purchasability_errors(supplier, customer, quantity):
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
        step = self.purchase_multiple or self._sales_unit.quantity_step
        return self._sales_unit.round(step)

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
        return self._sales_unit.round(self.minimum_purchase_quantity)

    @property
    def display_quantity_step(self):
        """
        Quantity step of this shop product in the display unit.

        Note: This can never be smaller than the display precision.
        """
        return max(
            self.unit.to_display(self.quantity_step),
            self.unit.display_precision)

    @property
    def display_quantity_minimum(self):
        """
        Quantity minimum of this shop product in the display unit.

        Note: This can never be smaller than the display precision.
        """
        return max(
            self.unit.to_display(self.minimum_purchase_quantity),
            self.unit.display_precision)

    @property
    def unit(self):
        """
        Unit of this product.

        :rtype: shuup.core.models.UnitInterface
        """
        return UnitInterface(self._sales_unit, self.display_unit)

    @property
    def _sales_unit(self):
        return self.product.sales_unit or PiecesSalesUnit()

    @property
    def images(self):
        return self.product.media.filter(shops=self.shop, kind=ProductMediaKind.IMAGE).order_by("ordering")

    @property
    def public_images(self):
        return self.images.filter(public=True)

    def get_supplier(self, customer=None, quantity=None, shipping_address=None):
        supplier_strategy = cached_load("SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY")
        kwargs = {
            "shop_product": self,
            "customer": customer,
            "quantity": quantity,
            "shipping_address": shipping_address
        }
        return supplier_strategy().get_supplier(**kwargs)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return self._safe_get_string("name")

    def get_description(self):
        return self._safe_get_string("description")

    def get_short_description(self):
        return self._safe_get_string("short_description")

    def _safe_get_string(self, key):
        return (
            self.safe_translation_getter(key, any_language=True)
            or self.product.safe_translation_getter(key, any_language=True)
        )


ShopProductLogEntry = define_log_model(ShopProduct)
