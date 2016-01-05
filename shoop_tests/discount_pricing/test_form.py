# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.core.models import Shop
from shoop.discount_pricing.admin_form_part import DiscountPricingForm
from shoop.discount_pricing.models import DiscountedProductPrice
from shoop.testing.factories import create_product, get_default_shop
from shoop_tests.utils.forms import get_form_data


def _get_test_product(product_price=125, discounted_price=108):
    shop = get_default_shop()
    product = create_product("Just-A-Pricing-Product", shop, default_price=product_price)
    DiscountedProductPrice.objects.create(product=product, shop=shop, price_value=discounted_price)
    return product

@pytest.mark.django_db
def test_basic_form_sanity():
    shop = get_default_shop()
    product = _get_test_product()
    frm = DiscountPricingForm(product=product, empty_permitted=True)
    assert len(frm.shops) == Shop.objects.count()
    assert "s_%d" % shop.id in frm.fields


@pytest.mark.django_db
def test_no_changes_into_form():
    product = _get_test_product()
    shop = get_default_shop()
    frm = DiscountPricingForm(product=product, empty_permitted=True)
    form_data = get_form_data(frm, prepared=True)
    frm = DiscountPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert DiscountedProductPrice.objects.get(product=product, shop=shop).price.value == 108

@pytest.mark.django_db
def test_change_shop_price():
    product = _get_test_product()
    shop = get_default_shop()

    form_field = "s_%d" % shop.id

    frm = DiscountPricingForm(product=product, empty_permitted=True)
    form_data = get_form_data(frm, prepared=True)
    # Price hike time!
    form_data[form_field] = "120"
    frm = DiscountPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert DiscountedProductPrice.objects.get(product=product, shop=shop).price.value == 120

    # Never mind actually, same price for all shops
    form_data[form_field] = ""
    frm = DiscountPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()

    assert not DiscountedProductPrice.objects.filter(product=product, shop=shop).exists()


@pytest.mark.django_db
def test_clear_prices():
    product = _get_test_product()
    # We can clear the prices out, can't we?
    form_data = {}
    frm = DiscountPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert not DiscountedProductPrice.objects.filter(product=product).exists()
