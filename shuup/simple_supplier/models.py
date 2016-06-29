# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import MoneyValueField, QuantityField
from shuup.core.settings import SHUUP_HOME_CURRENCY
from shuup.utils.properties import PriceProperty


class StockAdjustment(models.Model):
    product = models.ForeignKey("shuup.Product", related_name="+", on_delete=models.CASCADE, verbose_name=_("product"))
    supplier = models.ForeignKey("shuup.Supplier", on_delete=models.CASCADE, verbose_name=_("supplier"))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, verbose_name=_("created by"))
    delta = QuantityField(default=0, verbose_name=_("delta"))
    purchase_price_value = MoneyValueField(default=0)
    purchase_price = PriceProperty("purchase_price_value", "currency", "includes_tax")

    @property
    def currency(self):
        return SHUUP_HOME_CURRENCY

    @property
    def includes_tax(self):
        return False


class StockCount(models.Model):
    product = models.ForeignKey(
        "shuup.Product", related_name="+", editable=False, on_delete=models.CASCADE, verbose_name=_("product"))
    supplier = models.ForeignKey(
        "shuup.Supplier", editable=False, on_delete=models.CASCADE, verbose_name=_("supplier"))
    logical_count = QuantityField(default=0, editable=False, verbose_name=_("logical count"))
    physical_count = QuantityField(default=0, editable=False, verbose_name=_("physical count"))
    stock_value_value = MoneyValueField(default=0)
    stock_value = PriceProperty("stock_value_value", "currency", "includes_tax")
    stock_unit_price = PriceProperty("stock_unit_price_value", "currency", "includes_tax")

    class Meta:
        unique_together = [("product", "supplier")]

    @property
    def currency(self):
        return SHUUP_HOME_CURRENCY

    @property
    def includes_tax(self):
        return False

    @property
    def stock_unit_price_value(self):
        return (self.stock_value_value / self.logical_count if self.logical_count else 0)
