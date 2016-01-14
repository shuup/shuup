# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import QuantityField


class StockAdjustment(models.Model):
    product = models.ForeignKey("shoop.Product", related_name="+", on_delete=models.CASCADE, verbose_name=_("product"))
    supplier = models.ForeignKey("shoop.Supplier", on_delete=models.CASCADE, verbose_name=_("supplier"))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, verbose_name=_("created by"))
    delta = QuantityField(default=0, verbose_name=_("delta"))

    class Meta:
        unique_together = [("product", "supplier")]


class StockCount(models.Model):
    product = models.ForeignKey(
        "shoop.Product", related_name="+", editable=False, on_delete=models.CASCADE, verbose_name=_("product"))
    supplier = models.ForeignKey(
        "shoop.Supplier", editable=False, on_delete=models.CASCADE, verbose_name=_("supplier"))
    logical_count = QuantityField(default=0, editable=False, verbose_name=_("logical count"))
    physical_count = QuantityField(default=0, editable=False, verbose_name=_("physical count"))

    class Meta:
        unique_together = [("product", "supplier")]
