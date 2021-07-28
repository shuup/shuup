# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest
import random

from shuup.discounts.models import Discount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_discount_amount(rf):
    shop = factories.get_default_shop()
    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    assert request.shop == shop

    original_price = 10
    product = factories.create_product("test1", shop=shop, default_price=original_price)

    # Set discount percentage to 20% which means $2
    discount_percentage = 0.20
    discount = Discount.objects.create(active=True, product=product, discount_percentage=discount_percentage, shop=shop)
    assert product.get_price_info(request).price == request.shop.create_price(8)

    # Let's set discounted price to let's say $5
    discounted_price = 5
    discount = Discount.objects.create(active=True, product=product, discounted_price_value=discounted_price, shop=shop)
    assert product.get_price_info(request).price == request.shop.create_price(5)

    # All discount amount values up to $5 shouldn't change the product price
    for x in range(0, 5):
        discount_amount = decimal.Decimal(random.randrange(1, 501)) / 100
        discount = Discount.objects.create(
            active=True, product=product, discount_amount_value=discount_amount, shop=shop
        )
        assert product.get_price_info(request).price == request.shop.create_price(5)

    # Finally let's set discount amount value higher than all other discounts
    discount_amount = decimal.Decimal(random.randrange(500, 1000)) / 100
    discount = Discount.objects.create(active=True, product=product, discount_amount_value=discount_amount, shop=shop)
    assert product.get_price_info(request).price == request.shop.create_price(original_price - discount_amount)

    # Let's make sure price doesn't go below zero
    discount_amount = decimal.Decimal(random.randrange(1000, 25000)) / 100
    discount = Discount.objects.create(active=True, product=product, discount_amount_value=discount_amount, shop=shop)
    assert product.get_price_info(request).price == request.shop.create_price(0)

    # Finally let's make sure the minimum price value for shop product is honored
    shop_product = product.get_shop_instance(shop)
    min_price = decimal.Decimal(random.randrange(1, 501)) / 100
    shop_product.minimum_price_value = min_price
    shop_product.save()
    assert product.get_price_info(request).price == request.shop.create_price(min_price)
