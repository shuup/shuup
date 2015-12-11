# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings

from shoop.core.pricing import get_pricing_module, TaxfulPrice, TaxlessPrice
from shoop.discount_pricing.models import DiscountedProductPrice
from shoop.discount_pricing.module import DiscountPricingModule
from shoop.testing.factories import create_product, get_shop

pytestmark = pytest.mark.skipif("shoop.discount_pricing" not in settings.INSTALLED_APPS,
                                reason="Discount pricing not installed")

original_pricing_module = settings.SHOOP_PRICING_MODULE


def setup_module(module):
    settings.SHOOP_PRICING_MODULE = "discount_pricing"


def teardown_module(module):
    settings.SHOOP_PRICING_MODULE = original_pricing_module


def test_module_is_active():
    """
    Check that DiscountPricingModule is active.
    """
    module = get_pricing_module()
    assert isinstance(module, DiscountPricingModule)


def initialize_test(rf, include_tax=False):
    request = rf.get("/")
    request.shop = get_shop(prices_include_tax=include_tax)
    return request

# Tests for Discount Pricing

@pytest.mark.django_db
def test_price_infos_are_discounted(rf):
    request = initialize_test(rf, True)

    price = request.shop.create_price

    product_one = create_product("Product_1", request.shop, default_price=150)
    product_two = create_product("Product_2", request.shop, default_price=250)

    spp = DiscountedProductPrice(product=product_one, shop=request.shop, price_value=100)
    spp.save()

    spp = DiscountedProductPrice(product=product_two, shop=request.shop, price_value=200)
    spp.save()

    product_ids = [product_one.pk, product_two.pk]

    dpm = get_pricing_module()
    pricing_context = dpm.get_context_from_request(request)
    price_infos = dpm.get_price_infos(pricing_context, product_ids)

    assert len(price_infos) == 2
    assert product_one.pk in price_infos
    assert product_two.pk in price_infos

    first_price_info = price_infos[product_one.pk]
    second_price_info = price_infos[product_two.pk]

    assert first_price_info.price == price(100)
    assert first_price_info.base_price == price(150)
    assert first_price_info.is_discounted

    assert second_price_info.price == price(200)
    assert second_price_info.base_price == price(250)
    assert second_price_info.is_discounted



@pytest.mark.django_db
def test_price_is_discounted(rf):
    request = initialize_test(rf, False)
    shop = request.shop

    product = create_product("random-1", shop=shop, default_price=100)

    DiscountedProductPrice.objects.create(product=product, shop=shop, price_value=50)

    price_info = product.get_price_info(request)

    assert price_info.price == shop.create_price(50)

# These are basic tests for pricing module "copied" from Simple Pricing
@pytest.mark.django_db
def test_shop_specific_cheapest_price_1(rf):
    request = initialize_test(rf, False)
    price = request.shop.create_price

    product = create_product("Just-A-Product", request.shop, default_price=200)

    DiscountedProductPrice.objects.create(product=product, shop=request.shop, price_value=250)

    # Cheaper price is valid even if shop-specific discount exists
    assert product.get_price(request, quantity=1) == price(200)

@pytest.mark.django_db
def test_shop_specific_cheapest_price_2(rf):
    request = initialize_test(rf, False)
    price = request.shop.create_price

    product = create_product("Just-A-Product-Too", request.shop, default_price=199)

    DiscountedProductPrice.objects.create(product=product, shop=request.shop, price_value=250)

    # Cheaper price is valid even if the other way around applies
    assert product.get_price(request, quantity=1) == price(199)


@pytest.mark.django_db
def test_set_taxful_price_works(rf):
    request = initialize_test(rf, True)
    price = request.shop.create_price

    product = create_product("Anuva-Product", request.shop, default_price=300)

    # create ssp with higher price
    spp = DiscountedProductPrice(product=product, shop=request.shop, price_value=250)
    spp.save()

    price_info = product.get_price_info(request, quantity=1)

    assert price_info.price == price(250)

    assert product.get_price(request, quantity=1) == price(250)


@pytest.mark.django_db
def test_set_taxful_price_works_with_product_id(rf):
    request = initialize_test(rf, True)
    price = request.shop.create_price

    product = create_product("Anuva-Product", request.shop, default_price=300)

    # create ssp with higher price
    spp = DiscountedProductPrice(product=product, shop=request.shop, price_value=250)
    spp.save()

    price_info = product.get_price_info(request, quantity=1)

    assert price_info.price == price(250)

    assert product.get_price(request, quantity=1) == price(250)


@pytest.mark.django_db
def test_zero_default_price(rf):
    request = initialize_test(rf, True)
    price = request.shop.create_price

    # create a product with zero price
    product = create_product("random-1", shop=request.shop, default_price=0)

    DiscountedProductPrice.objects.create(product=product, shop=request.shop, price_value=50)

    price_info = product.get_price_info(request)

    assert price_info.price == price(0)

    assert product.get_price(request) == price(0)
