# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
import json
from decimal import Decimal

import pytest
import six
from django.utils.encoding import force_text

from shuup.core.models import get_person_contact, Order
from shuup.reports.forms import DateRangeChoices
from shuup.reports.writer import get_writer_instance
from shuup.default_reports.reports import SalesReport, TotalSales, SalesPerHour
from shuup.testing.factories import (
    create_random_person, get_default_shop, get_default_product, UserFactory
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.core.test_basic_order import create_order
from shuup_tests.reports.test_reports import initialize_report_test


class TestInfo(object):
    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

def initialize_simple_report(cls, data_overrides={}):
    product_price = 100
    product_count = 2
    tax_rate = Decimal("0.10")
    line_count = 1
    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(
        product_price, product_count, tax_rate, line_count)
    data = {
        "report": cls.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "json",
        "force_download": 1,
    }
    data.update(data_overrides)

    report = cls(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    return TestInfo(**{
        "expected_taxful_total": expected_taxful_total,
        "expected_taxless_total": expected_taxless_total,
        "json_data": json_data,
        "product_count": product_count,
        "shop": shop,
        "writer": writer,
        "report": report,
        "order": order,
    })


@pytest.mark.django_db
def test_sales_report(rf):
    test_info = initialize_simple_report(SalesReport)

    assert force_text(SalesReport.title) in test_info.json_data.get("heading")
    totals = test_info.json_data.get("tables")[0].get("totals")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert int(totals.get("product_count", 0)) == test_info.product_count
    assert int(return_data.get("product_count", 0)) == test_info.product_count
    assert int(totals.get("order_count", 0)) == 1
    assert int(return_data.get("order_count", 0)) == 1
    assert str(test_info.expected_taxless_total) in totals.get("taxless_total", "0")
    assert str(test_info.expected_taxful_total) in totals.get("taxful_total", "0")


@pytest.mark.django_db
def test_total_sales_report(rf):
    test_info = initialize_simple_report(TotalSales)
    assert force_text(TotalSales.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert return_data.get("currency") == test_info.shop.currency
    assert return_data.get("name") == test_info.shop.name
    assert int(return_data.get("order_amount")) == 1
    assert str(test_info.expected_taxful_total) in return_data.get("total_sales")


@pytest.mark.django_db
def test_total_sales_report_with_zero_total(rf):
    new_customer = create_random_person()  # This customer shouldn't have any sales
    test_info = initialize_simple_report(TotalSales, data_overrides={"customer": [new_customer]})
    assert force_text(TotalSales.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert return_data.get("currency") == test_info.shop.currency
    assert return_data.get("name") == test_info.shop.name
    assert int(return_data.get("order_amount")) == 0
    assert str(test_info.shop.create_price(0)) in return_data.get("total_sales")


@pytest.mark.django_db
def test_total_sales_per_hour_report(rf):
    test_info = initialize_simple_report(SalesPerHour)
    assert force_text(SalesPerHour.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")
    order_hour = test_info.order.order_date.strftime("%H")

    assert len(return_data) == 23 # all hours present
    for hour_data in return_data:
        if int(hour_data.get("hour")) == int(order_hour):
            assert str(test_info.expected_taxful_total) in hour_data.get("total_sales")
        else:
            assert hour_data.get("total_sales") == "0"


@pytest.mark.django_db
def test_contact_filters(rf, admin_user):
    shop = get_default_shop()
    products_per_order = 5

    request = rf.get('/')
    request.shop = shop
    apply_request_middleware(request)
    product = get_default_product()

    customer = get_person_contact(admin_user)
    create_order(request, creator=admin_user, customer=customer, product=product)
    order_one = Order.objects.first()

    user = UserFactory()
    second_customer = get_person_contact(user)
    create_order(request, creator=admin_user, customer=second_customer, product=product)
    order_two = Order.objects.first()

    user = UserFactory()
    user.is_staff = True
    user.save()

    create_order(request, creator=user, customer=second_customer, product=product)
    order_three = Order.objects.first()
    order_three.orderer = customer
    order_three.save()

    # test that admin user gets two orders as he created two
    expected_taxful_total_price = order_one.taxful_total_price + order_two.taxful_total_price
    expected_taxless_total_price = order_one.taxless_total_price + order_two.taxless_total_price
    expected_order_count = 2
    test_info = initialize_simple_report(SalesReport, data_overrides={"creator": [admin_user.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data)

    # test that new admin user gets one order
    expected_taxful_total_price = order_three.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price
    expected_order_count = 1
    test_info = initialize_simple_report(SalesReport, data_overrides={"creator": [user.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(expected_order_count, expected_taxful_total_price, expected_taxless_total_price,products_per_order, return_data)

    # test that new admin user and second_customer gets one order
    expected_taxful_total_price = order_three.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price
    expected_order_count = 1
    test_info = initialize_simple_report(SalesReport, data_overrides={"creator": [user.pk], "customer": [second_customer.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data)

    # test that second_customer gets two orders
    expected_taxful_total_price = order_three.taxful_total_price + order_two.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price + order_two.taxless_total_price
    expected_order_count = 2
    test_info = initialize_simple_report(SalesReport, data_overrides={"customer": [second_customer.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data)

    # test that second_customer gets two orders
    expected_taxful_total_price = order_three.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price
    expected_order_count = 1
    test_info = initialize_simple_report(SalesReport, data_overrides={"customer": [second_customer.pk], "orderer": [customer.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data)


def _assert_expected_values(expected_order_count, expected_taxful_total_price, expected_taxless_total_price,
                         products_per_order, return_data):
    assert len(return_data) == 1  # only one row since both are on same day
    assert int(return_data[0].get("order_count")) == expected_order_count
    assert int(return_data[0].get("product_count")) == products_per_order * expected_order_count
    assert return_data[0].get("taxful_total") == str(expected_taxful_total_price)
    assert return_data[0].get("taxless_total") == str(expected_taxless_total_price)
