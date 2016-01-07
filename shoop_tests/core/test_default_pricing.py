# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings

from shoop.core.pricing import get_pricing_module
from shoop.core.pricing.default_pricing import DefaultPricingModule
from shoop.testing.factories import (
    create_product, create_random_person, get_default_customer_group,
    get_default_shop
)

original_pricing_module = settings.SHOOP_PRICING_MODULE


def setup_module(module):
    settings.SHOOP_PRICING_MODULE = "default_pricing"


def teardown_module(module):
    settings.SHOOP_PRICING_MODULE = original_pricing_module


def get_shop_with_tax(include_tax):
    shop = get_default_shop()
    shop.prices_include_tax = include_tax
    shop.save()
    return shop


def initialize_test(rf, include_tax=False):
    shop = get_shop_with_tax(include_tax=include_tax)

    group = get_default_customer_group()
    customer = create_random_person()
    customer.groups.add(group)
    customer.save()

    request = rf.get("/")
    request.shop = shop
    request.customer = customer
    return request, shop, group


def test_module_is_active():  # this test is because we want to make sure `SimplePricing` is active
    module = get_pricing_module()
    assert isinstance(module, DefaultPricingModule)


@pytest.mark.django_db
def test_default_price_none_allowed(rf):
    request, shop, group = initialize_test(rf, False)
    shop = get_default_shop()
    product = create_product("test-product", shop=shop, default_price=None)
    assert product.get_price(request) == shop.create_price(0)


@pytest.mark.django_db
def test_default_price_zero_allowed(rf):
    request, shop, group = initialize_test(rf, False)
    shop = get_default_shop()
    product = create_product("test-product", shop=shop, default_price=0)
    assert product.get_price(request) == shop.create_price(0)


@pytest.mark.django_db
def test_default_price_value_allowed(rf):
    request, shop, group = initialize_test(rf, False)
    shop = get_default_shop()
    product = create_product("test-product", shop=shop, default_price=100)
    assert product.get_price(request) == shop.create_price(100)


@pytest.mark.django_db
def test_non_one_quantity(rf):
    request, shop, group = initialize_test(rf, False)
    shop = get_default_shop()
    product = create_product("test-product", shop=shop, default_price=100)
    assert product.get_price(request, quantity=5) == shop.create_price(500)
