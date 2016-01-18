# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models

from shoop.core.fields import QuantityField


class ProductPackageLink(models.Model):
    parent = models.ForeignKey("Product", related_name='+', on_delete=models.CASCADE)
    child = models.ForeignKey("Product", related_name='+', on_delete=models.CASCADE)
    quantity = QuantityField(default=1)

    class Meta:
        unique_together = (("parent", "child",), )
