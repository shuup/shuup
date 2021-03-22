# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from uuid import uuid4

from shuup.core.fields import MoneyValueField, QuantityField
from shuup.core.models import Category, OrderLineType, PolymorphicShuupModel, Product, ShopProduct
from shuup.core.order_creator._source import LineSource


class BasketLineEffect(PolymorphicShuupModel):
    identifier = None
    model = None
    admin_form_class = None

    campaign = models.ForeignKey(
        on_delete=models.CASCADE, to="BasketCampaign", related_name="line_effects", verbose_name=_("campaign")
    )

    def get_discount_lines(self, order_source, original_lines, supplier):
        """
        Applies the effect based on given `order_source`

        :return: amount of discount to accumulate for the product
        :rtype: Iterable[shuup.core.order_creator.SourceLine]
        """
        raise NotImplementedError("Error! Not implemented: `BasketLineEffect` -> `get_discount_lines()`")


class FreeProductLine(BasketLineEffect):
    identifier = "free_product_line_effect"
    model = Product
    name = _("Free Product(s)")

    quantity = QuantityField(default=1, verbose_name=_("quantity"))
    products = models.ManyToManyField(Product, verbose_name=_("product"))

    @property
    def description(self):
        return _("Select product(s) to give free.")

    @property
    def values(self):
        return self.products

    @values.setter
    def values(self, values):
        self.products = values

    def get_discount_lines(self, order_source, original_lines, supplier):
        lines = []
        shop = order_source.shop
        for product in self.products.all():
            try:
                shop_product = product.get_shop_instance(shop, allow_cache=True)
            except ShopProduct.DoesNotExist:
                continue

            if not supplier:
                supplier = shop_product.get_supplier(
                    order_source.customer, self.quantity, order_source.shipping_address
                )

            if not shop_product.is_orderable(
                supplier=supplier, customer=order_source.customer, quantity=self.quantity, allow_cache=False
            ):
                continue

            line_data = dict(
                line_id="free_product_%s" % uuid4().hex,
                type=OrderLineType.PRODUCT,
                quantity=self.quantity,
                shop=shop,
                text=("%s (%s)" % (product.name, self.campaign.public_name)),
                base_unit_price=shop.create_price(0),
                product=product,
                sku=product.sku,
                supplier=supplier,
                line_source=LineSource.DISCOUNT_MODULE,
            )
            lines.append(order_source.create_line(**line_data))
        return lines


class DiscountFromProduct(BasketLineEffect):
    identifier = "discount_from_product_line_effect"
    model = Product
    name = _("Discount from Product")

    per_line_discount = models.BooleanField(
        default=True,
        verbose_name=_("per line discount"),
        help_text=_("Disable this if you want to give discount for each matched product."),
    )

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True, verbose_name=_("discount amount"), help_text=_("Flat amount of discount.")
    )

    products = models.ManyToManyField(Product, verbose_name=_("product"))

    @property
    def description(self):
        return _("Select discount amount and products.")

    def get_discount_lines(self, order_source, original_lines, supplier):
        product_ids = self.products.values_list("pk", flat=True)
        campaign = self.campaign
        if not supplier:
            supplier = getattr(campaign, "supplier", None)

        for line in original_lines:
            if supplier and line.supplier != supplier:
                continue
            if not line.type == OrderLineType.PRODUCT:
                continue
            if line.product.pk not in product_ids:
                continue

            base_price = line.base_unit_price.value * line.quantity
            amnt = (self.discount_amount * line.quantity) if not self.per_line_discount else self.discount_amount

            # we use min() to limit the amount of discount to the products price
            discount_price = order_source.create_price(min(base_price, amnt))

            if not line.discount_amount or line.discount_amount < discount_price:
                line.discount_amount = discount_price

            # check for minimum price, if set, and change the discount amount
            _limit_discount_amount_by_min_price(line, order_source)

        return []


class DiscountFromCategoryProducts(BasketLineEffect):
    identifier = "discount_from_category_products_line_effect"
    model = Category
    name = _("Discount from Category products")

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True, verbose_name=_("discount amount"), help_text=_("Flat amount of discount.")
    )
    discount_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        blank=True,
        null=True,
        verbose_name=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."),
    )
    category = models.ForeignKey(on_delete=models.CASCADE, to=Category, verbose_name=_("category"))

    @property
    def description(self):
        return _(
            "Select discount amount and category. "
            "Please note that the discount will be given to all matching products in basket."
        )

    def get_discount_lines(self, order_source, original_lines, supplier):  # noqa (C901)
        if not (self.discount_percentage or self.discount_amount):
            return []

        campaign = self.campaign
        if not supplier:
            supplier = getattr(campaign, "supplier", None)

        product_ids = self.category.shop_products.values_list("product_id", flat=True)
        for line in original_lines:  # Use original lines since we don't want to discount free product lines
            if supplier and line.supplier != supplier:
                continue

            if not line.type == OrderLineType.PRODUCT:
                continue
            if line.product.variation_parent:
                if line.product.variation_parent.pk not in product_ids and line.product.pk not in product_ids:
                    continue
            else:
                if line.product.pk not in product_ids:
                    continue

            amount = order_source.zero_price.value
            base_price = line.base_unit_price.value * line.quantity

            if self.discount_amount:
                amount = self.discount_amount * line.quantity
            elif self.discount_percentage:
                amount = base_price * self.discount_percentage

            # we use min() to limit the amount of discount to base price
            # also in percentage, since one can configure 150% of discount
            discount_price = order_source.create_price(min(base_price, amount))

            if not line.discount_amount or line.discount_amount < discount_price:
                line.discount_amount = discount_price

            # check for minimum price, if set, and change the discount amount
            _limit_discount_amount_by_min_price(line, order_source)

        return []


def _limit_discount_amount_by_min_price(line, order_source):
    """
    Changes the Order Line discount amount if the
    discount amount exceeds the minimium total price set by
    `minimum_price` constraint in `ShopProduct`.

    :param shuup.core.order_creator.SourceLine line: the line to limit the discount
    :param shuup.core.order_source.OrderSource order_source: the order source
    """

    # make sure the discount respects the minimum price of the product, if set
    try:
        shop_product = line.product.get_shop_instance(order_source.shop, allow_cache=True)

        if shop_product.minimum_price:
            min_total = shop_product.minimum_price.value * line.quantity
            base_price = line.base_unit_price.value * line.quantity

            # check if the discount makes the line less than the minimum total
            if (base_price - line.discount_amount.value) < min_total:
                line.discount_amount = order_source.create_price(base_price - min_total)

    except ShopProduct.DoesNotExist:
        pass
