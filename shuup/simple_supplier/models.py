# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField

from shuup.core.fields import MoneyValueField, QuantityField
from shuup.core.settings_provider import ShuupSettings
from shuup.core.suppliers.enums import StockAdjustmentType
from shuup.utils.properties import PriceProperty


def _get_currency():
    from shuup.core.models import Shop

    if not ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
        return Shop.objects.first().currency
    return settings.SHUUP_HOME_CURRENCY


def _get_prices_include_tax():
    from shuup.core.models import Shop

    if not ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
        return Shop.objects.first().prices_include_tax
    return False


class StockAdjustment(models.Model):
    product = models.ForeignKey(
        "shuup.Product", related_name="stock_adjustments", on_delete=models.CASCADE, verbose_name=_("product")
    )
    supplier = models.ForeignKey("shuup.Supplier", on_delete=models.CASCADE, verbose_name=_("supplier"))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, verbose_name=_("created by")
    )
    delta = QuantityField(default=0, verbose_name=_("delta"))
    purchase_price_value = MoneyValueField(default=0)
    purchase_price = PriceProperty("purchase_price_value", "currency", "includes_tax")
    type = EnumIntegerField(
        StockAdjustmentType, db_index=True, default=StockAdjustmentType.INVENTORY, verbose_name=_("type")
    )

    @cached_property
    def currency(self):
        return _get_currency()

    @cached_property
    def includes_tax(self):
        return _get_prices_include_tax()


class StockCount(models.Model):
    alert_limit = QuantityField(default=0, editable=False, verbose_name=_("alert limit"))
    stock_managed = models.BooleanField(
        verbose_name=_("stock managed"),
        default=True,
        help_text=_("Use this to override the supplier default stock behavior per product."),
    )
    product = models.ForeignKey(
        "shuup.Product",
        related_name="simple_supplier_stock_count",
        editable=False,
        on_delete=models.CASCADE,
        verbose_name=_("product"),
    )
    supplier = models.ForeignKey("shuup.Supplier", editable=False, on_delete=models.CASCADE, verbose_name=_("supplier"))
    logical_count = QuantityField(default=0, editable=False, verbose_name=_("logical count"))
    physical_count = QuantityField(default=0, editable=False, verbose_name=_("physical count"))
    stock_value_value = MoneyValueField(default=0)
    stock_value = PriceProperty("stock_value_value", "currency", "includes_tax")
    stock_unit_price = PriceProperty("stock_unit_price_value", "currency", "includes_tax")

    class Meta:
        unique_together = [("product", "supplier")]

    @cached_property
    def currency(self):
        return _get_currency()

    @cached_property
    def includes_tax(self):
        return _get_prices_include_tax()

    @property
    def stock_unit_price_value(self):
        return self.stock_value_value / self.logical_count if self.logical_count else 0
