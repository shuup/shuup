# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import random

import pytest

from shuup.discounts.models import Discount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_discounted_price(rf):
    shop = factories.get_default_shop()
    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    assert request.shop == shop

    original_price = 10
    product = factories.create_product("test1", shop=shop, default_price=original_price)

    # Set discount with discount amount for $2
    discount_amount = 2
    discount = Discount.objects.create(active=True, product=product, discount_amount_value=discount_amount)
    discount.shops.add(shop)
    assert product.get_price_info(request).price == request.shop.create_price(8)

    # Set discount for 50% this is better than $2 and total of $5
    discount_percentage = 0.50
    discount = Discount.objects.create(active=True, product=product, discount_percentage=discount_percentage)
    discount.shops.add(shop)
    assert product.get_price_info(request).price == request.shop.create_price(5)

    # Ok now the actual test let's set the discounted price between 5 and 10
    # and it shouldn't become active since the 50% base discount
    for x in range(0, 5):
        discounted_price = decimal.Decimal(random.randrange(501, 1000))/100
        discount = Discount.objects.create(active=True, product=product, discounted_price_value=discounted_price)
        discount.shops.add(shop)
        assert product.get_price_info(request).price == request.shop.create_price(5)

    assert product.get_price_info(request).price == request.shop.create_price(5)
    # And then finally let's set the lowest discounted price
    discounted_price = decimal.Decimal(random.randrange(0, 500))/100
    discount = Discount.objects.create(active=True, product=product, discounted_price_value=discounted_price)
    discount.shops.add(shop)
    assert product.get_price_info(request).price == request.shop.create_price(discounted_price)
