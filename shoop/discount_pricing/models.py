# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import MoneyValueField


class DiscountedProductPrice(models.Model):
    product = models.ForeignKey("shoop.Product", related_name="+")
    shop = models.ForeignKey("shoop.Shop", db_index=True)
    price = MoneyValueField()

    # TODO: (TAX) Check includes_tax consistency (see below)
    #
    # DiscountedProductPrice entries in single shop should all have same
    # value of includes_tax, because inconsistencies in taxfulness of
    # prices may cause basket totals to be unsummable, since taxes are
    # unknown before customer has given their address and TaxfulPrice
    # cannot be summed with TaxlessPrice.

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
