# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.campaigns.models import BasketDiscountEffect
from shoop.core.models import OrderLineType, Product
from shoop.core.order_creator._source import LineSource


class BasketLineEffect(BasketDiscountEffect):

    class Meta:
        abstract = True

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
    yields = True
    name = _("Free Product(s)")

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
                quantity=1,
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
