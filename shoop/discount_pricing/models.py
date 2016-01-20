# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import MoneyValueField
from shoop.utils.properties import MoneyPropped, PriceProperty


class DiscountedProductPrice(MoneyPropped, models.Model):
    product = models.ForeignKey("shoop.Product", related_name="+", on_delete=models.CASCADE, verbose_name=_('product'))
    shop = models.ForeignKey("shoop.Shop", db_index=True, on_delete=models.CASCADE, verbose_name=_('shop'))
    price = PriceProperty("price_value", "shop.currency", "shop.prices_include_tax")
    price_value = MoneyValueField(verbose_name=_('price'))

    class Meta:
        unique_together = (('product', 'shop'),)
        verbose_name = _(u"product price")
        verbose_name_plural = _(u"product prices")

    def __repr__(self):
        return "<DiscountedProductPrice (p%s,s%s,g%s): price %s" % (
            self.product_id,
            self.shop_id,
            self.group_id,
            self.price,
        )
