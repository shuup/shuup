# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models

from shuup.core.fields import MoneyValueField
from shuup.utils.properties import MoneyPropped, PriceProperty


class SupplierPrice(MoneyPropped, models.Model):
    shop = models.ForeignKey(on_delete=models.CASCADE, to="shuup.Shop")
    supplier = models.ForeignKey(on_delete=models.CASCADE, to="shuup.Supplier")
    product = models.ForeignKey(on_delete=models.CASCADE, to="shuup.Product")
    amount_value = MoneyValueField()
    amount = PriceProperty("amount_value", "shop.currency", "shop.prices_include_tax")
