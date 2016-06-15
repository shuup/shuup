# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.campaigns.models import BasketCampaign, Coupon
from shoop.campaigns.models.basket_conditions import BasketTotalProductAmountCondition
from shoop.campaigns.models.basket_line_effects import FreeProductLine
from shoop.core.models import OrderLineType
from shoop.core.order_creator._source import LineSource
from shoop.front.basket import get_basket
from shoop.testing.factories import create_product, get_default_supplier
from shoop_tests.campaigns import initialize_test
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_basket_free_product(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "10"

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.save()

    second_product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)

    rule = BasketTotalProductAmountCondition.objects.create(value="2")

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    effect = FreeProductLine.objects.create(campaign=campaign)
    effect.products.add(second_product)


    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2

    line_types = [l.type for l in final_lines]
    assert OrderLineType.DISCOUNT not in line_types

    for line in basket.get_final_lines():
        assert line.type == OrderLineType.PRODUCT
        if line.product != product:
            assert line.product == second_product
            assert line.line_source == LineSource.DISCOUNT_MODULE
        else:
            assert line.line_source == LineSource.CUSTOMER


@pytest.mark.django_db
def test_basket_free_product_coupon(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "10"

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.save()

    second_product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)

    rule = BasketTotalProductAmountCondition.objects.create(value="2")
    coupon = Coupon.objects.create(code="TEST", active=True)

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test", coupon=coupon)
    campaign.conditions.add(rule)

    effect = FreeProductLine.objects.create(campaign=campaign)
    effect.products.add(second_product)

    basket.add_code(coupon.code)

    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2

    line_types = [l.type for l in final_lines]
    assert OrderLineType.DISCOUNT not in line_types

    for line in basket.get_final_lines():
        assert line.type == OrderLineType.PRODUCT

        if line.product != product:
            assert line.product == second_product
