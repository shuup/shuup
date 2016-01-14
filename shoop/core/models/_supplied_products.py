# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import QuantityField


class SuppliedProduct(models.Model):
    supplier = models.ForeignKey("Supplier", on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    sku = models.CharField(db_index=True, max_length=128, verbose_name=_('SKU'))
    alert_limit = models.IntegerField(default=0, verbose_name=_('alert limit'))
    physical_count = QuantityField(editable=False, verbose_name=_('physical stock count'))
    logical_count = QuantityField(editable=False, verbose_name=_('logical stock count'))

    class Meta:
        unique_together = (("supplier", "product", ), )
