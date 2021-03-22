# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from decimal import Decimal
from django.db import IntegrityError

from shuup.campaigns.admin_module.forms import BasketCampaignForm
from shuup.campaigns.models.basket_conditions import (
    BasketTotalAmountCondition,
    BasketTotalProductAmountCondition,
    CategoryProductsBasketCondition,
    ProductsInBasketCondition,
)
from shuup.campaigns.models.basket_effects import BasketDiscountAmount, BasketDiscountPercentage
from shuup.campaigns.models.basket_line_effects import DiscountFromCategoryProducts
from shuup.campaigns.models.campaigns import BasketCampaign, Coupon, CouponUsage
from shuup.core.defaults.order_statuses import create_default_order_statuses
from shuup.core.models import Category, OrderLineType, Shop, ShopProduct, ShopStatus, Supplier
from shuup.core.order_creator import OrderCreator
from shuup.front.basket import get_basket
from shuup.front.basket.commands import handle_add_campaign_code, handle_remove_campaign_code
from shuup.testing.factories import (
    CategoryFactory,
    create_default_tax_rule,
    create_product,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_default_tax,
    get_initial_order_status,
    get_shipping_method,
    get_tax,
)
from shuup_tests.campaigns import initialize_test
from shuup_tests.core.test_order_creator import seed_source
from shuup_tests.utils import printable_gibberish

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
    supplier = get_default_supplier(shop)

    single_product_price = "50"
    discount_amount_value = "10"

    # create basket rule that requires 2 products in basket
    basket_rule1 = BasketTotalProductAmountCondition.objects.create(value="2")

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    assert basket.product_count == 1

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign.conditions.add(basket_rule1)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_value)

    assert len(basket.get_final_lines()) == 2  # case 1
    assert basket.total_price == price(single_product_price)  # case 1

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.save()

    assert len(basket.get_final_lines()) == 3  # case 1
    assert basket.product_count == 2
    assert basket.total_price == (price(single_product_price) * basket.product_count - price(discount_amount_value))
    assert OrderLineType.DISCOUNT in [l.type for l in basket.get_final_lines()]

    # Make sure disabling campaign disables it conditions
    assert campaign.conditions.filter(active=True).exists()
    campaign.active = False
    campaign.save()
    assert not campaign.conditions.filter(active=True).exists()


@pytest.mark.django_db
def test_basket_category_discount(rf):
    """
    Test that discounting based on product category works.
    """

    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    category = CategoryFactory()

    discount_amount_value = 6
    single_product_price = 10

    def create_category_product(category):
        product = create_product(printable_gibberish(), shop, supplier, single_product_price)
        product.primary_category = category

        sp = ShopProduct.objects.get(product=product, shop=shop)
        sp.primary_category = category
        sp.categories.add(category)

        return product

    basket_condition = CategoryProductsBasketCondition.objects.create(quantity=2)
    basket_condition.categories.add(category)

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign.conditions.add(basket_condition)
    campaign.save()

    DiscountFromCategoryProducts.objects.create(
        campaign=campaign, discount_amount=discount_amount_value, category=category
    )
    basket.save()

    products = [create_category_product(category) for i in range(2)]
    for product in products:
        basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
        basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    assert basket.product_count == 2
    assert basket_condition.matches(basket=basket, lines=basket.get_lines())
    assert campaign.rules_match(basket, basket.get_lines())
    assert basket.total_price == price(single_product_price * 2) - price(discount_amount_value * 2)


@pytest.mark.django_db
def test_basket_campaign_case2(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier(shop)
    # create a basket rule that requires at least value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    single_product_price = "50"
    discount_amount_value = "10"

    unique_shipping_method = get_shipping_method(shop, price=50)

    for x in range(3):
        product = create_product(
            printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price
        )
        basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    assert basket.product_count == 3

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign.conditions.add(rule)
    campaign.save()

    BasketDiscountAmount.objects.create(discount_amount=discount_amount_value, campaign=campaign)

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
    supplier = get_default_supplier(shop)
    # create a basket rule that requires atleast value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    product_price = "200"

    discount1 = "10"
    discount2 = "20"  # should be selected
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)

    campaign1 = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign1.conditions.add(rule)
    campaign1.save()
    BasketDiscountAmount.objects.create(discount_amount=discount1, campaign=campaign1)

    campaign2 = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign2.conditions.add(rule)
    campaign2.save()
    BasketDiscountAmount.objects.create(discount_amount=discount2, campaign=campaign2)

    assert len(basket.get_final_lines()) == 3

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
    supplier = get_default_supplier(shop)
    # create a basket rule that requires atleast value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    product_price = "200"

    discount1 = "10"
    discount2 = "20"
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign.conditions.add(rule)
    campaign.save()

    BasketDiscountAmount.objects.create(discount_amount=discount1, campaign=campaign)

    dc = Coupon.objects.create(code="TEST", active=True)
    campaign2 = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", coupon=dc, active=True)

    BasketDiscountAmount.objects.create(discount_amount=discount2, campaign=campaign2)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    resp = handle_add_campaign_code(request, basket, dc.code)
    assert resp.get("ok")

    discount_lines_values = [
        line.discount_amount for line in basket.get_final_lines() if line.type == OrderLineType.DISCOUNT
    ]
    assert price(discount1) in discount_lines_values
    assert price(discount2) in discount_lines_values
    assert basket.total_price == (price(product_price) * basket.product_count - price(discount1) - price(discount2))

    assert basket.codes == [dc.code]

    # test code removal
    resp = handle_remove_campaign_code(request, basket, dc.code)
    assert resp.get("ok")

    assert basket.codes == []
    discount_lines_values = [
        line.discount_amount for line in basket.get_final_lines() if line.type == OrderLineType.DISCOUNT
    ]
    assert price(discount1) in discount_lines_values
    assert not price(discount2) in discount_lines_values


@pytest.mark.django_db
def test_percentage_campaign(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    basket = get_basket(request)
    supplier = get_default_supplier(shop)
    # create a basket rule that requires at least value of 200
    rule = BasketTotalAmountCondition.objects.create(value="200")

    product_price = "200"

    discount_percentage = "0.1"

    expected_discounted_price = price(product_price) - (price(product_price) * Decimal(discount_percentage))

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    campaign.conditions.add(rule)
    campaign.save()

    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage=discount_percentage)

    assert len(basket.get_final_lines()) == 3
    assert basket.product_count == 1
    assert basket.total_price == expected_discounted_price


@pytest.mark.django_db
def test_order_creation_adds_usage(rf, admin_user):
    request, shop, group = initialize_test(rf, False)

    source = seed_source(admin_user, shop)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(shop),
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

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test", coupon=coupon)
    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage="0.1")

    source.add_code(coupon.code)

    creator = OrderCreator()
    creator.create_order(source)

    assert CouponUsage.objects.count() == 1


@pytest.mark.django_db
def test_coupon_uniqueness(rf):
    request, shop, group = initialize_test(rf, False)
    first_campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test", coupon=None)

    second_campaign = BasketCampaign.objects.create(
        active=True, shop=shop, name="test1", public_name="test1", coupon=None
    )

    BasketDiscountPercentage.objects.create(campaign=first_campaign, discount_percentage="0.1")
    BasketDiscountPercentage.objects.create(campaign=second_campaign, discount_percentage="0.1")

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


@pytest.mark.django_db
def test_product_basket_campaigns():
    shop = get_default_shop()
    product = create_product("test", shop, default_price=20)
    shop_product = product.get_shop_instance(shop)
    cat = Category.objects.create(name="test")
    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test")

    # no rules
    assert BasketCampaign.get_for_product(shop_product).count() == 0

    # category condition that doesn't match
    cat_condition = CategoryProductsBasketCondition.objects.create()
    cat_condition.categories.add(cat)
    campaign.conditions.add(cat_condition)
    assert BasketCampaign.get_for_product(shop_product).count() == 0

    # category condition that matches
    shop_product.categories.add(cat)
    assert BasketCampaign.get_for_product(shop_product).count() == 1

    # category effect that doesn't match
    effect = DiscountFromCategoryProducts.objects.create(campaign=campaign, category=cat)
    shop_product.categories.remove(cat)
    shop_product.primary_category = None
    shop_product.save()

    campaign.line_effects.add(effect)
    assert BasketCampaign.get_for_product(shop_product).count() == 0

    # category effect and condition that matches
    shop_product.primary_category = cat
    shop_product.save()
    assert BasketCampaign.get_for_product(shop_product).count() == 1


@pytest.mark.django_db
def test_product_basket_campaigns2():
    shop = get_default_shop()
    product = create_product("test", shop, default_price=20)
    shop_product = product.get_shop_instance(shop)
    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test")

    condition = ProductsInBasketCondition.objects.create(quantity=1)
    campaign.conditions.add(condition)
    assert BasketCampaign.get_for_product(shop_product).count() == 0

    condition.products.add(product)
    assert BasketCampaign.get_for_product(shop_product).count() == 1

    shop1 = Shop.objects.create(
        name="testshop", identifier="testshop", status=ShopStatus.ENABLED, public_name="testshop"
    )
    sp = ShopProduct.objects.create(product=product, shop=shop1, default_price=shop1.create_price(200))

    campaign.shop = shop1
    campaign.save()
    assert BasketCampaign.get_for_product(shop_product).count() == 0
    assert BasketCampaign.get_for_product(sp).count() == 1


@pytest.mark.parametrize("include_tax", [True, False])
@pytest.mark.django_db
def test_percentage_campaign_full_discount(rf, include_tax):
    request, shop, group = initialize_test(rf, include_tax)
    create_default_order_statuses()
    tax = get_tax("sales-tax", "Sales Tax", Decimal(0.2))  # 20%
    create_default_tax_rule(tax)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=200)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.status = get_initial_order_status()

    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    # 100% of discount
    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage=Decimal(1))

    assert len(basket.get_final_lines()) == 3
    assert basket.product_count == 1
    assert basket.total_price.value == Decimal()

    order_creator = OrderCreator()
    order = order_creator.create_order(basket)
    order.create_payment(order.taxful_total_price)
    assert order.taxful_total_price.value == Decimal()


@pytest.mark.parametrize("include_tax", [True, False])
@pytest.mark.django_db
def test_percentage_campaign_different_supplier(rf, include_tax):
    request, shop, group = initialize_test(rf, include_tax)
    create_default_order_statuses()
    tax = get_tax("sales-tax", "Sales Tax", Decimal(0.2))  # 20%
    create_default_tax_rule(tax)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)
    supplier_2 = Supplier.objects.create(name="Supplier 2")

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=200)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.status = get_initial_order_status()

    # create a campaign for the Supplier 2
    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, supplier=supplier_2
    )
    # 100% of discount
    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage=Decimal(1))
    # discount is never applied
    lines_types = [line.type for line in basket.get_final_lines()]
    assert OrderLineType.DISCOUNT not in lines_types
    assert basket.product_count == 1
    assert basket.total_price.value == Decimal(200)


@pytest.mark.django_db
def test_percentage_campaign_different_coupon_supplier(rf):
    request, shop, group = initialize_test(rf, True)
    create_default_order_statuses()

    basket = get_basket(request)
    supplier = get_default_supplier(shop)
    supplier_2 = Supplier.objects.create(name="Supplier 2")

    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=200)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.status = get_initial_order_status()

    # Create coupon that is attached to Supplier 2
    coupon = Coupon.objects.create(code="QWERTY", shop=shop, active=True, supplier=supplier_2)
    # create basket with coupon code
    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, coupon=coupon, supplier=supplier_2
    )
    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage=Decimal(1))
    basket.add_code(coupon.code)

    # discount is never applied as there is no line
    # in the basket that matches the coupon's supplier
    lines_types = [line.type for line in basket.get_final_lines()]
    assert OrderLineType.DISCOUNT not in lines_types
    assert basket.product_count == 1
    assert basket.total_price.value == Decimal(200)

    # make supplier be the default supplier
    coupon.supplier = supplier
    coupon.save()
    campaign.supplier = supplier
    campaign.save()
    basket.uncache()

    lines_types = [line.type for line in basket.get_final_lines()]
    assert OrderLineType.DISCOUNT in lines_types
    assert basket.product_count == 1
    assert basket.total_price.value == Decimal()
