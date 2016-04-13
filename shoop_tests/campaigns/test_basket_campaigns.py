# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest

from django.db import IntegrityError

from shoop.campaigns.forms import BasketCampaignForm
from shoop.campaigns.models.basket_conditions import (
    BasketTotalProductAmountCondition, BasketTotalAmountCondition
)
from shoop.campaigns.models.campaigns import BasketCampaign, Coupon, CouponUsage
from shoop.core.models import OrderLineType
from shoop.core.order_creator import OrderCreator
from shoop.front.basket import get_basket
from shoop.front.basket.commands import handle_add_campaign_code
from shoop.testing.factories import (
    create_product, get_default_supplier, get_default_tax_class,
    get_default_product, get_shipping_method
)
from shoop_tests.campaigns import initialize_test
from shoop_tests.core.test_order_creator import seed_source
from shoop_tests.utils import printable_gibberish

"""
These tests provides proof for following requirements:
case 1: Define if this discount is available only if customer has X
    amount of products in their basket
case 2: Define if this discount is available if customer has products in
    their basket for certain amount of money (shipping excluded)
"""

@pytest.mark.django_db
def test_basket_campaign_module_case1(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "10"

     # create basket rule that requires 2 products in basket
    basket_rule1 = BasketTotalProductAmountCondition.objects.create(value="2")

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.save()

    assert basket.product_count == 1

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", discount_amount_value=discount_amount_value, active=True)
    campaign.conditions.add(basket_rule1)
    campaign.save()

    assert len(basket.get_final_lines()) == 1  # case 1
    assert basket.total_price == price(single_product_price) # case 1

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.save()

    assert len(basket.get_final_lines()) == 2  # case 1
    assert basket.product_count == 2
    assert basket.total_price == (price(single_product_price) * basket.product_count - price(discount_amount_value))
    assert OrderLineType.DISCOUNT in [l.type for l in basket.get_final_lines()]


@pytest.mark.django_db
def test_basket_campaign_case2(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()
     # create a basket rule that requires at least value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    single_product_price = "50"
    discount_amount_value = "10"

    unique_shipping_method = get_shipping_method(shop, price=50)

    for x in range(3):
        product = create_product(
            printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
        basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    assert basket.product_count == 3

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", discount_amount_value=discount_amount_value, active=True)
    campaign.conditions.add(rule)
    campaign.save()

    assert len(basket.get_final_lines()) == 3
    assert basket.total_price == price(single_product_price) * basket.product_count

    # check that shipping method affects campaign
    basket.shipping_method = unique_shipping_method
    basket.save()
    basket.uncache()
    assert len(basket.get_final_lines()) == 4  # Shipping should not affect the rule being triggered

    line_types = [l.type for l in basket.get_final_lines()]
    assert OrderLineType.DISCOUNT not in line_types

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    assert len(basket.get_final_lines()) == 6  # Discount included
    assert OrderLineType.DISCOUNT in [l.type for l in basket.get_final_lines()]


@pytest.mark.django_db
def test_only_cheapest_price_is_selected(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()
     # create a basket rule that requires atleast value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    product_price = "200"

    discount1 = "10"
    discount2 = "20"  # should be selected
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", discount_amount_value=discount1, active=True)
    campaign.conditions.add(rule)
    campaign.save()

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", discount_amount_value=discount2, active=True)
    campaign.conditions.add(rule)
    campaign.save()

    assert len(basket.get_final_lines()) == 2
    line_types = [l.type for l in basket.get_final_lines()]
    assert OrderLineType.DISCOUNT in line_types

    for line in basket.get_final_lines():
        if line.type == OrderLineType.DISCOUNT:
            assert line.discount_amount == price(discount2)


@pytest.mark.django_db
def test_multiple_campaigns_match_with_coupon(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()
     # create a basket rule that requires atleast value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    product_price = "200"

    discount1 = "10"
    discount2 = "20"
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", discount_amount_value=discount1, active=True)
    campaign.conditions.add(rule)
    campaign.save()

    dc = Coupon.objects.create(code="TEST", active=True)
    BasketCampaign.objects.create(
            shop=shop, public_name="test",
            name="test",
            coupon=dc,
            discount_amount_value=discount2,
            active=True
    )

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    resp = handle_add_campaign_code(request, basket, dc.code)
    assert resp.get("ok")

    discount_lines_values = [line.discount_amount for line in basket.get_final_lines()]
    assert price(discount1) in discount_lines_values
    assert price(discount2) in discount_lines_values
    assert basket.total_price == (price(product_price) * basket.product_count - price(discount1) - price(discount2))


@pytest.mark.django_db
def test_percentage_campaign(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier()
    # create a basket rule that requires at least value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    product_price = "200"

    discount_percentage = "0.1"

    expected_discounted_price = price(product_price) - (price(product_price) * Decimal(discount_percentage))

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", discount_percentage=discount_percentage, active=True)
    campaign.conditions.add(rule)
    campaign.save()

    assert len(basket.get_final_lines()) == 2
    assert basket.product_count == 1
    assert basket.total_price == expected_discounted_price


@pytest.mark.django_db
def test_order_creation_adds_usage(rf, admin_user):
    request, shop, group = initialize_test(rf, False)

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )

    # add coupon
    coupon = Coupon.objects.create(active=True, code="asdf")

    BasketCampaign.objects.create(
        active=True,
        shop=shop,
        name="test",
        public_name="test",
        discount_percentage="0.1",
        coupon=coupon)

    source.add_code(coupon.code)

    creator = OrderCreator()
    creator.create_order(source)

    assert CouponUsage.objects.count() == 1


@pytest.mark.django_db
def test_coupon_uniqueness(rf):
    request, shop, group = initialize_test(rf, False)
    first_campaign = BasketCampaign.objects.create(
        active=True,
        shop=shop,
        name="test",
        public_name="test",
        discount_percentage="0.1",
        coupon=None)

    second_campaign = BasketCampaign.objects.create(
        active=True,
        shop=shop,
        name="test1",
        public_name="test1",
        discount_percentage="0.1",
        coupon=None)

    coupon = Coupon.objects.create(active=True, code="test_code")
    first_campaign.coupon = coupon
    first_campaign.save()

    first_form = BasketCampaignForm(instance=first_campaign, request=request)
    assert len(first_form.fields["coupon"].choices) == 2  # coupon + empty

    second_form = BasketCampaignForm(instance=second_campaign, request=request)
    assert len(second_form.fields["coupon"].choices) == 1  # only empty

    # Can't set coupon for second campaign since coupon is unique
    with pytest.raises(IntegrityError):
        second_campaign.coupon = coupon
        second_campaign.save()
