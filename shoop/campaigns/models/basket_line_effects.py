# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import MoneyValueField
from shoop.core.models import OrderLineType, PolymorphicShoopModel, Product
from shoop.core.order_creator._source import LineSource


class BasketLineEffect(PolymorphicShoopModel):
    identifier = None
    model = None
    admin_form_class = None

    campaign = models.ForeignKey("BasketCampaign", related_name='line_effects', verbose_name=_("campaign"))

    def get_discount_lines(self, order_source, original_lines):
        """
        Applies the effect based on given `order_source`

        :return: amount of discount to accumulate for the product
        :rtype: Iterable[shoop.core.order_creator.SourceLine]
        """
        raise NotImplementedError("Not implemented!")


class FreeProductLine(BasketLineEffect):
    identifier = "free_product_line_effect"
    model = Product
    name = _("Free Product(s)")

    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantity"))
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

    def get_discount_lines(self, order_source, original_lines):
        lines = []
        shop = order_source.shop
        for product in self.products.all():
            shop_product = product.get_shop_instance(shop)
            supplier = shop_product.suppliers.first()
            if not shop_product.is_orderable(
                    supplier=supplier, customer=order_source.customer, quantity=1):
                continue
            line_data = dict(
                line_id="free_product_%s" % str(random.randint(0, 0x7FFFFFFF)),
                type=OrderLineType.PRODUCT,
                quantity=self.quantity,
                shop=shop,
                text=("%s (%s)" % (product.name, self.campaign.public_name)),
                base_unit_price=shop.create_price(0),
                product=product,
                sku=product.sku,
                supplier=supplier,
                line_source=LineSource.DISCOUNT_MODULE
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
        help_text=_("Uncheck this if you want to give discount for each matched product."))

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("discount amount"),
        help_text=_("Flat amount of discount."))

    products = models.ManyToManyField(Product, verbose_name=_("product"))

    @property
    def description(self):
        return _("Select discount amount and products.")

    def get_discount_lines(self, order_source, original_lines):
        product_ids = self.products.values_list("pk", flat=True)
        for line in original_lines:
            if not line.type == OrderLineType.PRODUCT:
                continue
            if line.product.pk not in product_ids:
                continue
            amnt = (self.discount_amount * line.quantity) if not self.per_line_discount else self.discount_amount
            line.discount_amount = order_source.create_price(amnt)
        return []
