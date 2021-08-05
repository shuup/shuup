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

    # Let's create discounted price $7
    discounted_price = 7
    discount = Discount.objects.create(active=True, product=product, discounted_price_value=discounted_price, shop=shop)
    assert product.get_price_info(request).price == request.shop.create_price(7)

    # Let's add higher discount amount for this discount
    discount_amount = decimal.Decimal(random.randrange(300, 800)) / 100
    discount.discount_amount_value = discount_amount
    discount.save()
    assert product.get_price_info(request).price == request.shop.create_price(original_price - discount_amount)

    # Let's make discount percentage between 80% to 90%
    discount_percentage = decimal.Decimal(random.randrange(80, 90)) / 100
    discount.discount_percentage = discount_percentage
    discount.save()
    assert product.get_price_info(request).price == request.shop.create_price(
        original_price - original_price * discount_percentage
    )

    # Let's add separate discount for 90% - 100% discount
    discount_percentage = decimal.Decimal(random.randrange(90, 100)) / 100
    discount = Discount.objects.create(active=True, product=product, discount_percentage=discount_percentage, shop=shop)
    assert product.get_price_info(request).price == request.shop.create_price(
        original_price - original_price * discount_percentage
    )

    # Finally let's make sure the minimum price value for shop product is honored
    shop_product = product.get_shop_instance(shop)
    min_price = decimal.Decimal(random.randrange(501, 701)) / 100
    shop_product.minimum_price_value = min_price
    shop_product.save()
    assert product.get_price_info(request).price == request.shop.create_price(min_price)
