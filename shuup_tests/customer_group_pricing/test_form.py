# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings

from shuup.core.models import ContactGroup, Shop
from shuup.customer_group_pricing.admin_form_part import \
    CustomerGroupPricingForm
from shuup.customer_group_pricing.models import CgpPrice
from shuup.testing.factories import (
    create_product, get_default_customer_group, get_default_shop
)
from shuup_tests.utils.forms import get_form_data

pytestmark = pytest.mark.skipif("shuup.customer_group_pricing" not in settings.INSTALLED_APPS,
                                reason="customer_group_pricing not installed")

def _get_test_product():
    shop = get_default_shop()
    product = create_product("Just-A-Pricing-Product", shop, default_price=200)
    CgpPrice.objects.create(
        product=product, shop=shop, group=get_default_customer_group(),
        price_value=250)
    return product


@pytest.mark.django_db
def test_basic_form_sanity():
    shop = get_default_shop()
    group = get_default_customer_group()
    product = _get_test_product()
    frm = CustomerGroupPricingForm(product=product, empty_permitted=True)
    assert len(frm.groups) == ContactGroup.objects.count()
    assert len(frm.shops) == Shop.objects.count()

    assert "s_%d_g_%d" % (shop.id, group.id) in frm.fields


@pytest.mark.django_db
def test_no_changes_into_form():
    product = _get_test_product()
    shop = get_default_shop()
    frm = CustomerGroupPricingForm(product=product, empty_permitted=True)
    # No changes made, right?
    form_data = get_form_data(frm, prepared=True)
    frm = CustomerGroupPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert CgpPrice.objects.get(product=product, shop=shop).price.value == 250


@pytest.mark.django_db
def test_change_shop_price():
    product = _get_test_product()
    shop = get_default_shop()
    group = get_default_customer_group()
    price = shop.create_price

    form_field = "s_%d_g_%d" % (shop.id, group.id)

    frm = CustomerGroupPricingForm(product=product, empty_permitted=True)
    form_data = get_form_data(frm, prepared=True)
    # Price hike time!
    form_data[form_field] = "4000"
    frm = CustomerGroupPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert CgpPrice.objects.get(product=product, shop=shop, group=group).price == price(4000)

    # Never mind actually, same price for all shops
    form_data[form_field] = ""
    frm = CustomerGroupPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()

    assert not CgpPrice.objects.filter(product=product, shop=shop, group=group).exists()


@pytest.mark.django_db
def test_clear_prices():
    product = _get_test_product()
    # We can clear the prices out, can't we?
    form_data = {}
    frm = CustomerGroupPricingForm(product=product, data=form_data, empty_permitted=True)
    frm.full_clean()
    frm.save()
    assert not CgpPrice.objects.filter(product=product).exists()
