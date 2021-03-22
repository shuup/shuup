# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.utils.encoding import force_text

from shuup.campaigns.models import CatalogCampaign, ProductFilter
from shuup.campaigns.models.basket_conditions import (
    BasketMaxTotalAmountCondition,
    BasketMaxTotalProductAmountCondition,
    BasketTotalAmountCondition,
    BasketTotalProductAmountCondition,
    BasketTotalUndiscountedProductAmountCondition,
    ChildrenProductCondition,
    ComparisonOperator,
    ProductsInBasketCondition,
)
from shuup.campaigns.models.basket_effects import BasketDiscountPercentage
from shuup.campaigns.models.campaigns import BasketCampaign
from shuup.core.models import OrderLineType, ProductMode, ProductVariationVariable, ProductVariationVariableValue
from shuup.front.basket import get_basket
from shuup.testing.factories import create_product, get_default_supplier
from shuup_tests.campaigns import initialize_test


@pytest.mark.django_db
def test_product_in_basket_condition(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product("Just-A-Product-Too", shop, default_price="200", supplier=supplier)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    condition = ProductsInBasketCondition.objects.create()
    condition.values = [product]
    condition.save()

    assert condition.values.first() == product
    assert condition.matches(basket, [])

    condition.quantity = 2
    condition.save()

    assert not condition.matches(basket, [])

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    assert condition.matches(basket, [])

    condition.operator = ComparisonOperator.EQUALS
    condition.save()

    assert condition.matches(basket, [])

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    assert not condition.matches(basket, [])


@pytest.mark.django_db
def test_product_in_basket_condition_with_variation_parent(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product(
        "test-product", shop, default_price="200", supplier=supplier, mode=ProductMode.SIMPLE_VARIATION_PARENT
    )

    child_products = []
    for x in range(0, 3):
        child_product = create_product("test-product-%s" % x, shop, default_price="10", supplier=supplier)
        child_product.link_to_parent(product)
        child_products.append(child_product)

    condition = ProductsInBasketCondition.objects.create()
    condition.values = [product]
    condition.operator = ComparisonOperator.EQUALS
    condition.quantity = 3
    condition.save()

    assert not condition.matches(basket, [])

    for child_product in child_products:
        basket.add_product(supplier=supplier, shop=shop, product=child_product, quantity=1)

    assert condition.matches(basket, [])


@pytest.mark.django_db
def test_basket_total_amount_conditions(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product("Just-A-Product-Too", shop, default_price="200", supplier=supplier)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    condition = BasketTotalAmountCondition.objects.create()
    condition.value = 1
    condition.save()
    assert condition.value == 1
    assert condition.matches(basket, [])

    condition2 = BasketMaxTotalAmountCondition.objects.create()
    condition2.value = 200
    condition2.save()

    assert condition2.matches(basket, [])

    condition2.value = 199
    condition2.save()

    assert not condition2.matches(basket, [])


@pytest.mark.django_db
def test_basket_total_value_conditions(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product("Just-A-Product-Too", shop, default_price="200", supplier=supplier)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    condition = BasketTotalProductAmountCondition.objects.create()
    condition.value = 1
    condition.save()
    assert condition.value == 1
    assert condition.matches(basket, [])
    assert "basket has at least the product count entered here" in force_text(condition.description)

    condition2 = BasketMaxTotalProductAmountCondition.objects.create()
    condition2.value = 1
    condition2.save()
    assert condition2.matches(basket, [])

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    assert not condition2.matches(basket, [])


@pytest.mark.django_db
def test_basket_total_undiscounted_value_conditions(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product("Just-A-Product", shop, default_price="150", supplier=supplier)
    discounted_product = create_product("Just-A-Second-Product", shop, default_price="200", supplier=supplier)

    # CatalogCampaign
    catalog_campaign = CatalogCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    # Limit catalog campaign to "discounted_product"
    product_filter = ProductFilter.objects.create()
    product_filter.products.add(discounted_product)
    catalog_campaign.filters.add(product_filter)

    basket.add_product(supplier=supplier, shop=shop, product=discounted_product, quantity=1)

    condition = BasketTotalUndiscountedProductAmountCondition.objects.create()
    condition.value = 1
    condition.save()
    assert not condition.matches(basket, [])

    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    assert condition.matches(basket, [])

    # Too high amount for undiscounted value
    condition.value = 151
    condition.save()

    assert not condition.matches(basket, [])


@pytest.mark.django_db
def test_product_child_condition_in_basket(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier(shop)

    product = create_product(
        "test-product", shop, default_price="200", supplier=supplier, mode=ProductMode.SIMPLE_VARIATION_PARENT
    )

    child_products = []
    for x in range(0, 3):
        child_product = create_product("test-product-%s" % x, shop, default_price="10", supplier=supplier)
        child_product.link_to_parent(product)
        child_products.append(child_product)

    condition = ChildrenProductCondition.objects.create()
    condition.product = product
    condition.save()

    assert not condition.matches(basket, [])

    for child_product in child_products:
        basket.add_product(supplier=supplier, shop=shop, product=child_product, quantity=1)

    assert condition.matches(basket, [])

    basket.clear_all()

    product = create_product(
        "test-product-rand", shop, default_price="200", supplier=supplier, mode=ProductMode.VARIABLE_VARIATION_PARENT
    )

    child_products = []
    color = ProductVariationVariable.objects.create(
        identifier="color",
        name="color",
        product=product,
        ordering=1,
    )
    for index, value in enumerate(["red", "green", "blue"]):
        ProductVariationVariableValue.objects.create(
            identifier=value,
            value=value,
            variable=color,
            ordering=index,
        )
    for x in range(3, 6):
        child_product = create_product("test-product-%s" % x, shop, default_price="10", supplier=supplier)
        child_product.link_to_parent(product, variables={"color": color.values.get(id=x - 2)})
        child_products.append(child_product)

    condition = ChildrenProductCondition.objects.create(active=True, product=product)
    condition.product = product
    condition.save()

    assert not condition.matches(basket, [])

    for child_product in child_products:
        basket.add_product(supplier=supplier, shop=shop, product=child_product, quantity=1)

    assert condition.matches(basket, [])
    basket.clear_all()

    # Add a discounted line to check if it'll go through
    discounted_product = create_product("discounted-product", shop, default_price="300", supplier=supplier)
    basket.add_product(supplier=supplier, shop=shop, product=discounted_product, quantity=2)
    assert len(basket.get_lines()) == 1
    base_unit_price = basket.shop.create_price("10.99")

    basket.add_line(
        text="Custom Line",
        type=OrderLineType.OTHER,
        line_id="not-important-but-unique",
        shop=basket.shop,
        quantity=1,
        base_unit_price=base_unit_price,
    )
    assert len(basket.get_lines()) == 2  # Assert a non-product line has been added
    assert not condition.matches(basket, [])
