# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.discounts.models import Discount
from shuup.discounts.utils import index_related_discount_shop_products


def reindex_discount(discount_id: int):
    discount = Discount.objects.get(pk=discount_id)
    index_related_discount_shop_products([discount])


def reindex_happy_hour(happy_hour_id: int):
    discounts = Discount.objects.filter(happy_hours=happy_hour_id)
    index_related_discount_shop_products(discounts)
