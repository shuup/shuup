# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.test.utils import override_settings
from django.utils.translation import activate

from shuup.core.fields.utils import ensure_decimal_places
from shuup.core.models import CustomerTaxGroup, OrderLineType
from shuup.core.order_creator import OrderCreator, TaxesNotCalculated
from shuup.testing.factories import (
    create_product,
    create_random_person,
    get_address,
    get_default_payment_method,
    get_default_product,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax,
    get_initial_order_status,
)
from shuup.utils.money import Money
from shuup.utils.numbers import bankers_round
from shuup_tests.campaigns.test_reports import seed_source
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


@pytest.mark.django_db
def test_customertaxgroup():
    activate("en")
    person_group = CustomerTaxGroup.get_default_person_group()
    assert CustomerTaxGroup.objects.count() == 1
    assert person_group.identifier == "default_person_customers"
    assert person_group.name == "Retail Customers"

    company_group = CustomerTaxGroup.get_default_company_group()
    assert CustomerTaxGroup.objects.count() == 2
    assert company_group.identifier == "default_company_customers"
    assert company_group.name == "Company Customers"


def get_source():
    source = BasketishOrderSource(get_default_shop())
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )
    return source


@pytest.mark.django_db
def test_calculate_taxes_automatically_setting():
    with override_settings(SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE=True):
        source = get_source()
        source.get_final_lines()
        assert source._taxes_calculated == True

        source = get_source()
        assert source._taxes_calculated == False
        source.calculate_taxes_or_raise()
        assert source._taxes_calculated == True

    with override_settings(SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE=False):
        source = get_source()
        source.get_final_lines()
        assert source._taxes_calculated == False

        with pytest.raises(TaxesNotCalculated):
            source.calculate_taxes_or_raise()


@pytest.mark.django_db
def test_broken_order(admin_user):
    """"""
    quantities = [44, 23, 65]
    expected = sum(quantities) * 50
    expected_based_on = expected / 1.5

    # Shuup is calculating taxes per line so there will be some "errors"
    expected_based_on = ensure_decimal_places(Decimal("%s" % (expected_based_on + 0.01)))

    shop = get_default_shop()

    supplier = get_default_supplier()
    product1 = create_product("simple-test-product1", shop, supplier, 50)
    product2 = create_product("simple-test-product2", shop, supplier, 50)
    product3 = create_product("simple-test-product3", shop, supplier, 50)

    tax = get_default_tax()

    source = BasketishOrderSource(get_default_shop())
    billing_address = get_address(country="US")
    shipping_address = get_address(name="Test street", country="US")
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = create_random_person()
    source.payment_method = get_default_payment_method()
    source.shipping_method = get_default_shipping_method()

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product1,
        supplier=get_default_supplier(),
        quantity=quantities[0],
        base_unit_price=source.create_price(50),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product2,
        supplier=get_default_supplier(),
        quantity=quantities[1],
        base_unit_price=source.create_price(50),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product3,
        supplier=get_default_supplier(),
        quantity=quantities[2],
        base_unit_price=source.create_price(50),
    )

    currency = "EUR"
    summary = source.get_tax_summary()

    assert len(summary) == 1
    summary = summary[0]

    assert summary.taxful == Money(expected, "EUR")
    assert summary.based_on == Money(expected_based_on, "EUR")

    # originally non-rounded value
    assert bankers_round(source.get_total_tax_amount()) == summary.tax_amount

    assert source.taxless_total_price.value == expected_based_on
    assert summary.taxful.value == source.taxful_total_price.value

    assert summary.tax_amount == Money(
        bankers_round(source.taxful_total_price.value - source.taxless_total_price.value), currency
    )
    assert summary.taxful == summary.raw_based_on + summary.tax_amount

    assert summary.tax_rate == tax.rate
    assert summary.taxful.value == (summary.based_on + summary.tax_amount).value - Decimal("%s" % 0.01)

    # create order from basket
    creator = OrderCreator()
    order = creator.create_order(source)
    assert order.taxless_total_price.value == expected_based_on

    # originally non-rounded value
    assert bankers_round(order.get_total_tax_amount()) == summary.tax_amount


@pytest.mark.django_db
def test_ignore_lines_from_other_sources():
    with override_settings(SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE=True):
        source1 = get_source()
        source2 = get_source()

        # get the tax summary from source1
        source1_summary = source1.get_tax_summary()
        assert len(source1_summary) == 1
        based_on_before = source1_summary[0].based_on

        # add line from order source2 in source1
        source1._lines.append(source2._lines[0])
        source1.uncache()

        # get the summary again, we should ignore lines
        # that are not from the same order source
        source1_summary = source1.get_tax_summary()
        assert len(source1_summary) == 1
        # nothing changed
        assert based_on_before == source1_summary[0].based_on
