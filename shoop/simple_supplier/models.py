# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models

from shoop.core.fields import QuantityField


class StockAdjustment(models.Model):
    product = models.ForeignKey("shoop.Product", related_name="+")
    supplier = models.ForeignKey("shoop.Supplier")
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT)
    delta = QuantityField(default=0)

    class Meta:
        unique_together = [("product", "supplier")]


class StockCount(models.Model):
    product = models.ForeignKey("shoop.Product", related_name="+", editable=False)
    supplier = models.ForeignKey("shoop.Supplier", editable=False)
    logical_count = QuantityField(default=0, editable=False)
    physical_count = QuantityField(default=0, editable=False)

    class Meta:
        unique_together = [("product", "supplier")]
