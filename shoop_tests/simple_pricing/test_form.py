# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.core.models import Shop
from shoop.core.models.contacts import ContactGroup
from shoop.simple_pricing.admin_form_part import SimplePricingForm
from shoop.testing.factories import get_default_shop, create_product, get_default_customer_group
from shoop.simple_pricing.models import SimpleProductPrice
from shoop_tests.utils.forms import get_form_data


def _get_test_product():
    shop = get_default_shop()
    product = create_product("Just-A-Pricing-Product")
    SimpleProductPrice.objects.create(product=product, shop=None, price=200, includes_tax=False)
    SimpleProductPrice.objects.create(product=product, shop=shop, price=250, includes_tax=False)
    return product


@pytest.mark.django_db
def test_basic_form_sanity():
    shop = get_default_shop()
    group = get_default_customer_group()
    product = _get_test_product()
    frm = SimplePricingForm(product=product, empty_permitted=True)
    assert len(frm.groups) == 1 + ContactGroup.objects.count()
    assert len(frm.shops) == 1 + Shop.objects.count()
    for shop_id in (0, shop.id):
        for group_id in (0, group.id):
            assert "s_%d_g_%d" % (shop_id, group_id) in frm.fields

    form_data = get_form_data(frm)
    assert form_data["s_%d_g_0" % shop.id] == 250
    assert form_data["s_0_g_0"] == 200


@pytest.mark.django_db
def test_no_changes_into_form():
    product = _get_test_product()
    shop = get_default_shop()
    frm = SimplePricingForm(product=product, empty_permitted=True)
    # No changes made, right?
    form_data = get_form_data(frm, prepared=True)
    frm = SimplePricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert SimpleProductPrice.objects.get(product=product, shop=None).price == 200
    assert SimpleProductPrice.objects.get(product=product, shop=shop).price == 250


@pytest.mark.django_db
def test_change_shop_price():
    product = _get_test_product()
    shop = get_default_shop()
    frm = SimplePricingForm(product=product, empty_permitted=True)
    form_data = get_form_data(frm, prepared=True)
    # Price hike time!
    form_data["s_%d_g_0" % shop.id] = "4000"
    frm = SimplePricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert SimpleProductPrice.objects.get(product=product, shop=None).price == 200
    assert SimpleProductPrice.objects.get(product=product, shop=shop).price == 4000

    # Never mind actually, same price for all shops
    form_data["s_%d_g_0" % shop.id] = ""
    frm = SimplePricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert SimpleProductPrice.objects.get(product=product, shop=None).price == 200
    assert not SimpleProductPrice.objects.filter(product=product, shop=shop).exists()


@pytest.mark.django_db
def test_clear_prices():
    product = _get_test_product()
    # We can clear the prices out, can't we?
    form_data = {}
    frm = SimplePricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert not SimpleProductPrice.objects.filter(product=product).exists()
