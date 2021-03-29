# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest

from shuup.campaigns.exceptions import CampaignsInvalidInstanceForCacheUpdate
from shuup.campaigns.models import BasketCampaign
from shuup.campaigns.models.basket_conditions import CategoryProductsBasketCondition, ComparisonOperator
from shuup.campaigns.models.basket_line_effects import DiscountFromCategoryProducts
from shuup.campaigns.signal_handlers import update_filter_cache
from shuup.front.basket import get_basket
from shuup.testing.factories import create_product, get_default_category, get_default_supplier, get_shipping_method
from shuup_tests.campaigns import initialize_test


@pytest.mark.django_db
def test_category_product_in_basket_condition(rf):
    request, shop, group = initialize_test(rf, False)
    basket = get_basket(request)
    supplier = get_default_supplier(shop)
    category = get_default_category()
    product = create_product("The Product", shop=shop, default_price="200", supplier=supplier)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)

    shop_product = product.get_shop_instance(shop)
    assert category not in shop_product.categories.all()

    condition = CategoryProductsBasketCondition.objects.create(operator=ComparisonOperator.EQUALS, quantity=1)
    condition.categories.add(category)

    # No match the product does not have the category
    assert not condition.matches(basket, [])

    category.shop_products.add(shop_product)
    assert condition.matches(basket, [])

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    assert not condition.matches(basket, [])

    condition.operator = ComparisonOperator.GTE
    condition.save()

    assert condition.matches(basket, [])

    condition.excluded_categories.add(category)
    assert not condition.matches(basket, [])

    with pytest.raises(CampaignsInvalidInstanceForCacheUpdate):
        update_filter_cache("test", shop)


@pytest.mark.django_db
def test_category_products_effect_with_amount(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    category = get_default_category()
    supplier = get_default_supplier(shop)

    single_product_price = "50"
    discount_amount_value = "10"
    quantity = 5

    product = create_product("The product", shop=shop, supplier=supplier, default_price=single_product_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(category)

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = CategoryProductsBasketCondition.objects.create(operator=ComparisonOperator.EQUALS, quantity=quantity)
    rule.categories.add(category)

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    DiscountFromCategoryProducts.objects.create(
        campaign=campaign, category=category, discount_amount=discount_amount_value
    )

    assert rule.matches(basket, [])
    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2  # no new lines since the effect touches original lines
    expected_discount_amount = quantity * basket.create_price(discount_amount_value)
    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount


@pytest.mark.django_db
def test_category_products_effect_with_percentage(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    category = get_default_category()
    supplier = get_default_supplier(shop)

    single_product_price = "50"
    discount_percentage = decimal.Decimal("0.10")
    quantity = 5

    product = create_product("The product", shop=shop, supplier=supplier, default_price=single_product_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(category)

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = CategoryProductsBasketCondition.objects.create(operator=ComparisonOperator.EQUALS, quantity=quantity)
    rule.categories.add(category)

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    DiscountFromCategoryProducts.objects.create(
        campaign=campaign, category=category, discount_percentage=discount_percentage
    )

    assert rule.matches(basket, [])
    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2  # no new lines since the effect touches original lines
    expected_discount_amount = quantity * basket.create_price(single_product_price) * discount_percentage
    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount
