# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.encoding import force_text

from shuup.campaigns.models.basket_conditions import (
    BasketMaxTotalAmountCondition, BasketMaxTotalProductAmountCondition,
    BasketTotalAmountCondition, BasketTotalProductAmountCondition,
    ComparisonOperator, ProductsInBasketCondition
)
from shuup.front.basket import get_basket
from shuup.testing.factories import create_product, get_default_supplier
from shuup_tests.campaigns import initialize_test


@pytest.mark.django_db
def test_product_in_basket_condition(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

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
def test_basket_total_amount_conditions(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

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
    supplier = get_default_supplier()

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
