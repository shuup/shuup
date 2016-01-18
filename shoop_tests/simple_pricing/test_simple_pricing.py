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
from shoop.simple_pricing.models import SimpleProductPrice
from shoop.simple_pricing.module import SimplePricingModule
from shoop.testing.factories import (
    create_product, create_random_person, get_default_customer_group, get_shop
)

pytestmark = pytest.mark.skipif("shoop.simple_pricing" not in settings.INSTALLED_APPS,
                                reason="Simple pricing not installed")

original_pricing_module = settings.SHOOP_PRICING_MODULE


def setup_module(module):
    settings.SHOOP_PRICING_MODULE = "simple_pricing"


def teardown_module(module):
    settings.SHOOP_PRICING_MODULE = original_pricing_module


def initialize_test(rf, include_tax=False):
    shop = get_shop(prices_include_tax=include_tax)

    group = get_default_customer_group()
    customer = create_random_person()
    customer.groups.add(group)
    customer.save()

    request = rf.get("/")
    request.shop = shop
    request.customer = customer
    return request, shop, group


def test_module_is_active():
    """
    Check that SimplePricingModule is active.
    """
    module = get_pricing_module()
    assert isinstance(module, SimplePricingModule)


@pytest.mark.django_db
def test_shop_specific_cheapest_price_1(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    product = create_product("Just-A-Product", shop, default_price=200)

    # SimpleProductPrice.objects.create(product=product, shop=None, price=200)
    SimpleProductPrice.objects.create(product=product, shop=shop, group=group, price_value=250)

    # Cheaper price is valid even if shop-specific price exists
    assert product.get_price(request, quantity=1) == price(200)


@pytest.mark.django_db
def test_shop_specific_cheapest_price_2(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=199)

    SimpleProductPrice.objects.create(product=product, shop=shop, group=group, price_value=250)

    # Cheaper price is valid even if the other way around applies
    assert product.get_price(request, quantity=1) == price(199)


@pytest.mark.django_db
def test_set_taxful_price_works(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("Anuva-Product", shop, default_price=300)

    # create ssp with higher price
    spp = SimpleProductPrice(product=product, shop=shop, group=group, price_value=250)
    spp.save()

    price_info = product.get_price_info(request, quantity=1)

    assert price_info.price == price(250)
    assert product.get_price(request, quantity=1) == price(250)


@pytest.mark.django_db
def test_set_taxful_price_works_with_product_id(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("Anuva-Product", shop, default_price=300)

    # create ssp with higher price
    spp = SimpleProductPrice(product=product, shop=shop, group=group, price_value=250)
    spp.save()

    price_info = product.get_price_info(request, quantity=1)

    assert price_info.price == price(250)

    assert product.get_price(request, quantity=1) == price(250)


@pytest.mark.django_db
def test_price_infos(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product_one = create_product("Product_1", shop, default_price=150)
    product_two = create_product("Product_2", shop, default_price=250)

    spp = SimpleProductPrice(product=product_one, shop=shop, group=group, price_value=100)
    spp.save()

    spp = SimpleProductPrice(product=product_two, shop=shop, group=group, price_value=200)
    spp.save()

    product_ids = [product_one.pk, product_two.pk]

    spm = get_pricing_module()
    assert isinstance(spm, SimplePricingModule)
    pricing_context = spm.get_context_from_request(request)
    price_infos = spm.get_price_infos(pricing_context, product_ids)

    assert len(price_infos) == 2
    assert product_one.pk in price_infos
    assert product_two.pk in price_infos

    assert price_infos[product_one.pk].price == price(100)
    assert price_infos[product_two.pk].price == price(200)

    assert price_infos[product_one.pk].base_price == price(100)
    assert price_infos[product_two.pk].base_price == price(200)


@pytest.mark.django_db
def test_no_customer(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("random-1", shop=shop, default_price=100)

    SimpleProductPrice.objects.create(product=product, group=group, shop=shop, price_value=50)

    request.customer = None

    price_info = product.get_price_info(request)

    assert price_info.price == price(100)


@pytest.mark.django_db
def test_zero_default_price(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    # create a product with zero price
    product = create_product("random-1", shop=shop, default_price=0)

    SimpleProductPrice.objects.create(product=product, group=group, shop=shop, price_value=50)

    price_info = product.get_price_info(request)

    assert price_info.price == price(50)
