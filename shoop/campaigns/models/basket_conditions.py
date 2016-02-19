# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from shoop.core.fields import MoneyValueField
from shoop.core.models import Product
from shoop.utils.properties import MoneyPropped, PriceProperty


class BasketCondition(PolymorphicModel):
    model = None
    active = models.BooleanField(default=True)
    name = _("Basket condition")

    def matches(self, basket, lines):
        return False

    def __str__(self):
        return force_text(self.name)


class BasketTotalProductAmountCondition(BasketCondition):
    identifier = "basket_product_condition"
    name = _("Basket product count")

    product_count = models.DecimalField(
        verbose_name=_("product count in basket"), blank=True, null=True, max_digits=36, decimal_places=9)

    def matches(self, basket, lines):
        return (basket.product_count >= self.product_count)

    @property
    def description(self):
        return _("Limit the campaign to match when basket has atleast the product count entered here.")

    @property
    def value(self):
        return self.product_count

    @value.setter
    def value(self, value):
        self.product_count = value


class BasketTotalAmountCondition(MoneyPropped, BasketCondition):
    identifier = "basket_amount_condition"
    name = _("Basket total value")

    amount = PriceProperty("amount_value", "campaign.shop.currency", "campaign.shop.prices_include_tax")
    amount_value = MoneyValueField(default=None, blank=True, null=True, verbose_name=_("basket total amount"))

    def matches(self, basket, lines):
        return (basket.total_price_of_products.value >= self.amount_value)

    @property
    def description(self):
        return _("Limit the campaign to match when it has at least the total value entered here worth of products.")

    @property
    def value(self):
        return self.amount_value

    @value.setter
    def value(self, value):
        self.amount_value = value


class ProductsInBasketCondition(BasketCondition):
    identifier = "basket_products_condition"
    name = _("Products in basket")

    model = Product

    products = models.ManyToManyField(Product, verbose_name=_("products"), blank=True)

    def matches(self, basket, lines):
        return any((product_id in basket.product_ids) for product_id in self.products.values_list("pk", flat=True))

    @property
    def description(self):
        return _("Limit the campaign to have the selected products in basket.")

    @property
    def values(self):
        return self.products

    @values.setter
    def values(self, value):
        self.products = value
