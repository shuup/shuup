# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.core.pricing.price import TaxfulPrice
from shoop.testing.factories import get_default_shop, create_product
from shoop.simple_pricing.module import SimplePricingModule
from shoop.simple_pricing.models import SimpleProductPrice


@pytest.mark.django_db
def test_shop_specific_cheapest_price_1(rf):
    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    product = create_product("Just-A-Product")
    SimpleProductPrice.objects.create(product=product, shop=None, price=200,)
    SimpleProductPrice.objects.create(product=product, shop=shop, price=250)
    spm = SimplePricingModule()
    assert spm.get_price(spm.get_context_from_request(request), product.pk, quantity=1) == TaxfulPrice(200)  # Cheaper price is valid even if shop-specific price exists


@pytest.mark.django_db
def test_shop_specific_cheapest_price_2(rf):
    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    product = create_product("Just-A-Product-Too")
    SimpleProductPrice.objects.create(product=product, shop=None, price=250)
    SimpleProductPrice.objects.create(product=product, shop=shop, price=199)
    spm = SimplePricingModule()
    assert spm.get_price(spm.get_context_from_request(request), product.pk, quantity=1) == TaxfulPrice(199)  # Cheaper price is valid even if the other way around applies


@pytest.mark.django_db
def test_set_taxful_price_works():
    product = create_product("Anuva-Product")
    spp = SimpleProductPrice(product=product, shop=None)
    spp.price = 250
    spp.includes_tax = True
    spp.save()
    assert spp.price == 250
    assert spp.includes_tax == True
    spm = SimplePricingModule()
    pp = spm.get_price(spm.get_context_from_data(), product.pk, quantity=1)
    assert pp.includes_tax
    assert pp == TaxfulPrice("250")
