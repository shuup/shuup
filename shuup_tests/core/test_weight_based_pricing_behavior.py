# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import pytest

from shuup.core.models import OrderLineType, WeightBasedPriceRange, WeightBasedPricingBehaviorComponent
from shuup.core.models._service_behavior import _is_in_range
from shuup.testing.factories import (
    create_product,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_supplier,
    get_shop,
    get_supplier,
)

from .test_order_creator import seed_source


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_service,service_attr",
    [(get_default_payment_method, "payment_method"), (get_default_shipping_method, "shipping_method")],
)
def test_with_one_matching_range(admin_user, get_service, service_attr):
    ranges_data = [
        (None, "10.32", decimal.Decimal("0.0001"), "Low range"),
        ("10.32", "32.45678", decimal.Decimal("10.000000"), "Mid range"),
        ("32.45678", None, decimal.Decimal("23.567"), "High range"),
    ]
    service = get_service()
    _assign_component_for_service(service, ranges_data)
    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("0"), "low")
    _test_service_ranges_against_source(source, service, decimal.Decimal("0.0001"), "Low range")

    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("32.45678"), "mid")
    _test_service_ranges_against_source(source, service, decimal.Decimal("10.000000"), "Mid range")

    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("32.456780001"), "high")
    _test_service_ranges_against_source(source, service, decimal.Decimal("23.567"), "High range")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_service,service_attr",
    [(get_default_payment_method, "payment_method"), (get_default_shipping_method, "shipping_method")],
)
def test_with_multiple_matching_ranges(admin_user, get_service, service_attr):
    ranges_data = [
        (None, "10.32", decimal.Decimal("0.0001"), "Low range"),
        ("10.00", "50.00", decimal.Decimal("10.000000"), "Mid range"),
        ("32.45678", None, decimal.Decimal("23.567"), "High range"),
        (None, None, decimal.Decimal("1000000"), "Expensive range"),
    ]
    service = get_service()
    _assign_component_for_service(service, ranges_data)

    # Low, mid and expensive ranges match but the lowest price is selected
    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("10.01"), "low")
    _test_service_ranges_against_source(source, service, decimal.Decimal("0.0001"), "Low range")

    # Mid, high and expensive ranges matches but the mid range is selected
    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("40"), "mid")
    _test_service_ranges_against_source(source, service, decimal.Decimal("10.000000"), "Mid range")

    # High and expensive ranges match but the mid range is selected
    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("100"), "high")
    _test_service_ranges_against_source(source, service, decimal.Decimal("23.567"), "High range")


def _assign_component_for_service(service, ranges_data):
    assert service.behavior_components.count() == 0
    component = WeightBasedPricingBehaviorComponent.objects.create()
    for min, max, price, description in ranges_data:
        WeightBasedPriceRange.objects.create(
            description=description, min_value=min, max_value=max, price_value=price, component=component
        )
    service.behavior_components.add(component)


def _test_service_ranges_against_source(source, service, target_price, target_description):
    assert service.behavior_components.count() == 1
    costs = list(service.get_costs(source))
    unavailability_reasons = list(service.get_unavailability_reasons(source))
    assert (unavailability_reasons or costs) and not (unavailability_reasons and costs)
    if costs:  # We have costs so let's test prices
        assert len(costs) == 1
        assert costs[0].price.value == target_price
        assert costs[0].description == target_description


def _get_source_for_weight(user, service, service_attr, total_gross_weight, sku, supplier=None):
    source = seed_source(user)
    supplier = supplier or get_default_supplier()
    product = create_product(
        sku=sku,
        shop=source.shop,
        supplier=supplier,
        default_price=3.33,
        **{"net_weight": decimal.Decimal("0"), "gross_weight": total_gross_weight}
    )
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(1),
    )
    setattr(source, service_attr, service)
    assert source.total_gross_weight == total_gross_weight
    assert getattr(source, service_attr) == service
    return source


def test_is_in_range():
    # value, min, max and whether the value should match withing the range
    test_data = [
        ("0", None, None, True),
        ("0", "0", None, True),
        ("0", None, "10.32", True),
        ("0", "0", "10.32", True),
        ("32.00", None, None, True),
        ("32.00", "0", None, True),
        ("32.00", None, "64", True),
        ("32.00", "0", "31.9999", False),
        ("32.00", "0", "32", True),
        ("32.00", "0", "64", True),
        ("32.00", "31.999", None, True),
        ("32.00", "31.999", "32.000", True),
        ("32.00", "31.999", "32.0001", True),
        ("32.00", "32.00", "32.00", True),
        ("32.00", "32.00", "66", False),
        ("32.00", "32.00", None, False),
        ("43.00", "32.00", "100.00", True),
        ("11.00", "32.00", "100.00", False),
        ("121.00", "32.00", "100.00", False),
    ]

    for value, min, max, result in test_data:
        assert (
            _is_in_range(
                decimal.Decimal(value), decimal.Decimal(min) if min else None, decimal.Decimal(max) if max else None
            )
            == result
        )
        # Any range with None value should be False
        assert not _is_in_range(None, decimal.Decimal(min) if min else None, decimal.Decimal(max) if max else None)
        # In case when both limits is given range shouldn't work in reverse order.
        if min and max and min != max:
            assert not _is_in_range(
                decimal.Decimal(value), decimal.Decimal(max) if max else None, decimal.Decimal(min) if min else None
            )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_service,service_attr",
    [(get_default_payment_method, "payment_method"), (get_default_shipping_method, "shipping_method")],
)
def test_out_of_range(admin_user, get_service, service_attr):
    ranges_data = [
        (None, "10.32", decimal.Decimal("0.0001"), "Low range"),
    ]
    service = get_service()
    _assign_component_for_service(service, ranges_data)

    # Low, mid and expensive ranges match but the lowest price is selected
    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("10.01"), "low")
    _test_service_ranges_against_source(source, service, decimal.Decimal("0.0001"), "Low range")

    # Mid, high and expensive ranges matches but the mid range is selected
    source = _get_source_for_weight(admin_user, service, service_attr, decimal.Decimal("40"), "mid")
    _test_service_ranges_against_source(source, service, decimal.Decimal("10.000000"), "Mid range")


@pytest.mark.django_db
def test_matching_range_different_suppliers(admin_user):
    supplier_1 = get_supplier("simple_supplier", name="Supplier 1", shop=get_shop())
    supplier_2 = get_supplier("simple_supplier", name="Supplier 2", shop=get_shop())

    # this service will only be available for supplier_2
    shipping_method = get_default_shipping_method()
    shipping_method.supplier = supplier_2
    shipping_method.save()

    ranges_data = [
        ("10", "20", decimal.Decimal("20"), "Mid range"),
    ]
    _assign_component_for_service(shipping_method, ranges_data)

    # as the shipping method is set for supplier_2, it shouldn't raise for items of supplier_1
    source = _get_source_for_weight(
        admin_user, shipping_method, "shipping_method", decimal.Decimal("3"), "sup1", supplier=supplier_1
    )
    assert not list(shipping_method.get_unavailability_reasons(source))
    assert not list(shipping_method.get_costs(source))

    # raise when correct supplier is set
    source = _get_source_for_weight(
        admin_user, shipping_method, "shipping_method", decimal.Decimal("3"), "sup2", supplier=supplier_2
    )
    assert list(shipping_method.get_unavailability_reasons(source))
    assert not list(shipping_method.get_costs(source))

    # don't raise with correct supplier and correct weight range
    source = _get_source_for_weight(
        admin_user, shipping_method, "shipping_method", decimal.Decimal("14"), "sup3", supplier=supplier_2
    )
    assert not list(shipping_method.get_unavailability_reasons(source))
    assert list(shipping_method.get_costs(source))
