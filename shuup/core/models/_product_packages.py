# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import QuantityField


class ProductPackageLink(models.Model):
    parent = models.ForeignKey(
        "Product",
        related_name='linked_packages_parent',
        on_delete=models.CASCADE,
        verbose_name=_("parent product")
    )
    child = models.ForeignKey(
        "Product",
        related_name='linked_packages_child',
        on_delete=models.CASCADE,
        verbose_name=_("child product")
    )
    quantity = QuantityField(default=1, verbose_name=_("quantity"))

    class Meta:
        unique_together = (("parent", "child",), )
