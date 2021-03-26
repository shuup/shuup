# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings

from shuup.core.models import ContactGroup, Shop
from shuup.customer_group_pricing.admin_form_part import CustomerGroupDiscountForm, CustomerGroupPricingForm
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice
from shuup.testing.factories import create_product, get_default_customer_group, get_default_shop
from shuup_tests.utils.forms import get_form_data

pytestmark = pytest.mark.skipif(
    "shuup.customer_group_pricing" not in settings.INSTALLED_APPS, reason="customer_group_pricing not installed"
)


def _get_test_product():
    shop = get_default_shop()
    product = create_product("Just-A-Pricing-Product", shop, default_price=200)
    CgpPrice.objects.create(product=product, shop=shop, group=get_default_customer_group(), price_value=250)
    CgpDiscount.objects.create(
        product=product, shop=shop, group=get_default_customer_group(), discount_amount_value=100
    )
    return product


@pytest.mark.parametrize("form", [CustomerGroupPricingForm, CustomerGroupDiscountForm])
@pytest.mark.django_db
def test_basic_form_sanity(form):
    shop = get_default_shop()
    group = get_default_customer_group()
    product = _get_test_product()

    kwargs = dict(product=product, shop=shop)
    frm = form(**kwargs)

    assert len(frm.groups) == ContactGroup.objects.count()

    assert "s_%d_g_%d" % (shop.id, group.id) in frm.fields


@pytest.mark.parametrize("form", [CustomerGroupPricingForm, CustomerGroupDiscountForm])
@pytest.mark.django_db
def test_no_changes_into_form(form):
    product = _get_test_product()
    shop = get_default_shop()

    frm = form(product=product, shop=shop)
    # No changes made, right?
    form_data = get_form_data(frm, prepared=True)
    frm = form(product=product, shop=shop, data=form_data)
    frm.full_clean()
    frm.save()

    if form == CustomerGroupPricingForm:
        assert CgpPrice.objects.get(product=product, shop=shop).price.value == 250
    else:
        assert CgpDiscount.objects.get(product=product, shop=shop).discount_amount.value == 100


@pytest.mark.parametrize("form", [CustomerGroupPricingForm, CustomerGroupDiscountForm])
@pytest.mark.django_db
def test_change_shop_price(form):
    product = _get_test_product()
    shop = get_default_shop()
    group = get_default_customer_group()
    price = shop.create_price

    form_field = "s_%d_g_%d" % (shop.id, group.id)
    frm = form(product=product, shop=shop)
    form_data = get_form_data(frm, prepared=True)

    if form == CustomerGroupPricingForm:
        form_data[form_field] = "4000"
    else:
        form_data[form_field] = "50"

    frm = form(product=product, shop=shop, data=form_data)
    frm.full_clean()
    frm.save()

    if form == CustomerGroupPricingForm:
        assert CgpPrice.objects.get(product=product, shop=shop, group=group).price == price(4000)
    else:
        assert CgpDiscount.objects.get(product=product, shop=shop, group=group).discount_amount == price(50)

    # Never mind actually, same price for all shops
    form_data[form_field] = ""

    frm = form(product=product, shop=shop, data=form_data)
    frm.full_clean()
    frm.save()

    if form == CustomerGroupPricingForm:
        assert not CgpPrice.objects.filter(product=product, shop=shop, group=group).exists()
    else:
        assert not CgpDiscount.objects.filter(product=product, shop=shop, group=group).exists()


@pytest.mark.parametrize("form", [CustomerGroupPricingForm, CustomerGroupDiscountForm])
@pytest.mark.django_db
def test_clear_prices(form):
    product = _get_test_product()
    shop = get_default_shop()
    # We can clear the prices out, can't we?
    form_data = {}
    frm = form(product=product, shop=shop, data=form_data)
    frm.full_clean()
    frm.save()

    if form == CustomerGroupPricingForm:
        assert not CgpPrice.objects.filter(product=product).exists()
    else:
        assert not CgpDiscount.objects.filter(product=product, shop=shop).exists()
