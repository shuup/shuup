# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import MoneyValueField
from shuup.core.utils.context_cache import bump_cache_for_product
from shuup.utils.properties import MoneyPropped, PriceProperty


class CgpBase(models.Model):
    product = models.ForeignKey("shuup.Product", related_name="+", on_delete=models.CASCADE, verbose_name=_("product"))
    shop = models.ForeignKey("shuup.Shop", db_index=True, on_delete=models.CASCADE, verbose_name=_("shop"))
    group = models.ForeignKey(
        "shuup.ContactGroup", db_index=True, on_delete=models.CASCADE, verbose_name=_("contact group"))

    class Meta:
        abstract = True
        unique_together = (('product', 'shop', 'group'),)


class CgpPrice(MoneyPropped, CgpBase):
    price = PriceProperty("price_value", "shop.currency", "shop.prices_include_tax")
    price_value = MoneyValueField(verbose_name=_("price"))

    class Meta(CgpBase.Meta):
        abstract = False
        verbose_name = _(u"product price")
        verbose_name_plural = _(u"product prices")

    def __repr__(self):
        return "<CgpPrice (p%s,s%s,g%s): price %s" % (
            self.product_id,
            self.shop_id,
            self.group_id,
            self.price,
        )

    def save(self, *args, **kwargs):
        super(CgpPrice, self).save(*args, **kwargs)

        # check if there is a shop product before bumping the cache
        if self.product.shop_products.filter(shop_id=self.shop.id).exists():
            bump_cache_for_product(self.product, self.shop)


class CgpDiscount(MoneyPropped, CgpBase):
    discount_amount = PriceProperty("discount_amount_value", "shop.currency", "shop.prices_include_tax")
    discount_amount_value = MoneyValueField(verbose_name=_("discount amount"))

    class Meta(CgpBase.Meta):
        abstract = False
        verbose_name = _(u"product discount")
        verbose_name_plural = _(u"product discounts")

    def __repr__(self):
        return "<CgpDiscount (p%s,s%s,g%s): discount %s" % (
            self.product_id,
            self.shop_id,
            self.group_id,
            self.discount_amount
        )

    def save(self, *args, **kwargs):
        super(CgpDiscount, self).save(*args, **kwargs)

        # check if there is a shop product before bumping the cache
        if self.product.shop_products.filter(shop_id=self.shop.id).exists():
            bump_cache_for_product(self.product, self.shop)
