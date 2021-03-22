# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest

from shuup.core.models import CountryLimitBehaviorComponent, OrderLineType, get_person_contact
from shuup.testing.factories import (
    create_product,
    get_address,
    get_default_supplier,
    get_initial_order_status,
    get_payment_method,
    get_shipping_method,
    get_shop,
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


@pytest.mark.django_db
@pytest.mark.parametrize(
    "countries,european_countries,not_in_countries,not_in_european_countries,shipping_country,available",
    [
        (["FI"], False, [], False, "FI", True),
        (["FI"], False, [], False, "SE", False),
        (["FI"], True, [], False, "SE", True),
        ([], True, ["SE"], False, "FI", True),
        ([], True, ["SE"], False, "SE", False),
        ([], False, [], True, "US", True),
        ([], False, [], True, "FI", False),
        (["US"], True, [], False, "US", True),
        ([], False, [], True, "USA", True),
        ([], False, [], True, "FI", False),
        (["SE", "DK", "EE"], False, [], False, "DK", True),
        (["SE", "DK", "EE"], False, [], False, "FI", False),
        ([], True, ["SE", "DK", "EE", "FI"], False, "FR", True),
        ([], True, ["SE", "DK", "EE", "FI"], False, "CA", False),
        ([], True, ["SE", "DK", "EE", "FI"], False, "EE", False),
    ],
)
def test_coutries_availability_for_shipping_method(
    admin_user, countries, european_countries, not_in_countries, not_in_european_countries, shipping_country, available
):
    source = _get_source(admin_user, shipping_country, "FI")
    shipping_method = source.shipping_method
    assert shipping_method.behavior_components.count() == 0
    component = CountryLimitBehaviorComponent.objects.create(
        available_in_countries=countries,
        available_in_european_countries=european_countries,
        unavailable_in_countries=not_in_countries,
        unavailable_in_european_countries=not_in_european_countries,
    )
    shipping_method.behavior_components.add(component)

    assert shipping_method.behavior_components.count() == 1
    unavailability_reasons = list(shipping_method.get_unavailability_reasons(source))
    assert bool(len(unavailability_reasons) == 0) == available
    shipping_method.behavior_components.clear()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "countries,european_countries,not_in_countries,not_in_european_countries,billing_country,available",
    [
        (["FI"], False, [], False, "FI", True),
        (["FI"], False, [], False, "SE", False),
        (["FI"], True, [], False, "SE", True),
        ([], True, ["SE"], False, "FI", True),
        ([], True, ["SE"], False, "SE", False),
        ([], False, [], True, "USA", True),
        ([], False, [], True, "FI", False),
        (["FI", "SE"], False, ["SE"], False, "FI", True),
        (["FI", "SE"], False, ["SE"], False, "SE", False),
    ],
)
def test_coutries_availability_for_payment_method(
    admin_user, countries, european_countries, not_in_countries, not_in_european_countries, billing_country, available
):
    source = _get_source(admin_user, "FI", billing_country)
    payment_method = source.payment_method
    assert payment_method.behavior_components.count() == 0
    component = CountryLimitBehaviorComponent.objects.create(
        available_in_countries=countries,
        available_in_european_countries=european_countries,
        unavailable_in_countries=not_in_countries,
        unavailable_in_european_countries=not_in_european_countries,
    )
    payment_method.behavior_components.add(component)

    assert payment_method.behavior_components.count() == 1
    unavailability_reasons = list(payment_method.get_unavailability_reasons(source))
    assert bool(len(unavailability_reasons) == 0) == available
    payment_method.behavior_components.clear()


def _get_source(user, shipping_country, billing_country):
    prices_include_taxes = True
    shop = get_shop(prices_include_taxes)
    payment_method = get_payment_method(shop)
    shipping_method = get_shipping_method(shop)
    source = _seed_source(shop, user, shipping_country, billing_country)
    source.payment_method = payment_method
    source.shipping_method = shipping_method
    assert source.payment_method_id == payment_method.id
    assert source.shipping_method_id == shipping_method.id

    supplier = get_default_supplier()
    product = create_product(
        sku="test-%s--%s" % (prices_include_taxes, 10), shop=source.shop, supplier=supplier, default_price=10
    )
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    assert payment_method == source.payment_method
    assert shipping_method == source.shipping_method
    return source


def _seed_source(shop, user, shipping_country, billing_country):
    source = BasketishOrderSource(shop)
    billing_address = get_address(country=billing_country)
    shipping_address = get_address(name="Test street", country=shipping_country)
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = get_person_contact(user)
    return source
