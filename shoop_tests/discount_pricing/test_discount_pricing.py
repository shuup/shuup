# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from shoop.core.pricing.price import TaxfulPrice, TaxlessPrice
from shoop.discount_pricing.models import DiscountedProductPrice
from shoop.discount_pricing.module import DiscountPricingModule
from shoop.testing.factories import get_default_shop, create_product
from shoop.core.pricing import get_pricing_module

pytestmark = pytest.mark.skipif("shoop.discount_pricing" not in settings.INSTALLED_APPS,
                                reason="Discount pricing not installed")

original_pricing_module = settings.SHOOP_PRICING_MODULE


def setup_module(module):
    settings.SHOOP_PRICING_MODULE = "discount_pricing"


def teardown_module(module):
    settings.SHOOP_PRICING_MODULE = original_pricing_module


def test_module_is_active():  # this test is because we want to make sure `SimplePricing` is active
    module = get_pricing_module()
    assert isinstance(module, DiscountPricingModule)

def get_shop_with_tax(include_tax):
    shop = get_default_shop()
    shop.prices_include_tax = include_tax
    shop.save()
    return shop

def initialize_test(rf, include_tax=False):
    request = rf.get("/")
    request.shop = get_shop_with_tax(include_tax=include_tax)
    return request

# Tests for Discount Pricing

@pytest.mark.django_db
def test_price_infos_are_discounted(rf):
    request = initialize_test(rf, True)

    product_one = create_product("Product_1", request.shop, default_price=150)
    product_two = create_product("Product_2", request.shop, default_price=250)

    spp = DiscountedProductPrice(product=product_one, shop=request.shop, price=100)
    spp.save()

    spp = DiscountedProductPrice(product=product_two, shop=request.shop, price=200)
    spp.save()

    product_ids = [product_one.pk, product_two.pk]

    dpm = DiscountPricingModule()
    pricing_context = dpm.get_context_from_request(request)
    price_infos = dpm.get_price_infos(pricing_context, product_ids)

    assert len(price_infos) == 2
    assert product_one.pk in price_infos
    assert product_two.pk in price_infos

    first_price_info = price_infos[product_one.pk]
    second_price_info = price_infos[product_two.pk]


    assert first_price_info.price == TaxfulPrice(100)
    assert first_price_info.base_price == TaxfulPrice(150)
    assert first_price_info.is_discounted

    assert second_price_info.price == TaxfulPrice(200)
    assert second_price_info.base_price == TaxfulPrice(250)
    assert second_price_info.is_discounted



@pytest.mark.django_db
def test_price_is_discounted(rf):
    shop = get_default_shop()

    product = create_product("random-1", shop=shop, default_price=100)

    DiscountedProductPrice.objects.create(product=product, shop=shop, price=50)

    request = rf.get("/")
    request.shop = shop

    dpm = DiscountPricingModule()
    pricing_context = dpm.get_context_from_request(request)

    price_info = dpm.get_price_info(pricing_context, product)

    assert price_info.price == TaxfulPrice(50)

# These are basic tests for pricing module "copied" from Simple Pricing
@pytest.mark.django_db
def test_shop_specific_cheapest_price_1(rf):
    request = initialize_test(rf, False)

    product = create_product("Just-A-Product", request.shop, default_price=200)

    # determine which is the taxfulness
    price_cls = TaxfulPrice if request.shop.prices_include_tax else TaxlessPrice

    # DiscountedProductPrice.objects.create(product=product, shop=None, price=200)
    DiscountedProductPrice.objects.create(product=product, shop=request.shop, price=250)
    dpm = DiscountPricingModule()
    assert product.get_price(dpm.get_context_from_request(request), quantity=1) == price_cls(
        200)  # Cheaper price is valid even if shop-specific discount exists

@pytest.mark.django_db
def test_shop_specific_cheapest_price_2(rf):
    request = initialize_test(rf, False)

    product = create_product("Just-A-Product-Too", request.shop, default_price=199)

    price_cls = (TaxfulPrice if request.shop.prices_include_tax else TaxlessPrice)

    DiscountedProductPrice.objects.create(product=product, shop=request.shop, price=250)
    dpm = DiscountPricingModule()
    assert product.get_price(dpm.get_context_from_request(request), quantity=1) == price_cls(
        199)  # Cheaper price is valid even if the other way around applies


@pytest.mark.django_db
def test_set_taxful_price_works(rf):
    request = initialize_test(rf, True)

    product = create_product("Anuva-Product", request.shop, default_price=300)

    # create ssp with higher price
    spp = DiscountedProductPrice(product=product, shop=request.shop, price=250)
    spp.save()

    dpm = DiscountPricingModule()
    pricing_context = dpm.get_context_from_request(request)
    price_info = product.get_price_info(pricing_context, quantity=1)

    assert price_info.price == TaxfulPrice(250)
    assert price_info.includes_tax

    pp = product.get_price(pricing_context, quantity=1)

    assert pp.includes_tax
    assert pp == TaxfulPrice("250")


@pytest.mark.django_db
def test_set_taxful_price_works_with_product_id(rf):
    request = initialize_test(rf, True)

    product = create_product("Anuva-Product", request.shop, default_price=300)

    # create ssp with higher price
    spp = DiscountedProductPrice(product=product, shop=request.shop, price=250)
    spp.save()

    dpm = DiscountPricingModule()
    pricing_context = dpm.get_context_from_request(request)
    price_info = dpm.get_price_info(pricing_context, product=product.pk, quantity=1)

    assert price_info.price == TaxfulPrice(250)
    assert price_info.includes_tax

    pp = product.get_price(pricing_context, quantity=1)

    assert pp.includes_tax
    assert pp == TaxfulPrice("250")



@pytest.mark.django_db
def test_zero_default_price(rf):
    request = initialize_test(rf, True)

    # create a product with zero price
    product = create_product("random-1", shop=request.shop, default_price=0)

    DiscountedProductPrice.objects.create(product=product, shop=request.shop, price=50)

    dpm = DiscountPricingModule()
    pricing_context = dpm.get_context_from_request(request)
    price_info = dpm.get_price_info(pricing_context, product)

    assert price_info.price == TaxfulPrice(0)
