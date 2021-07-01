# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
import pytz
import six
from babel.dates import format_date
from datetime import datetime
from decimal import Decimal
from django.test.utils import override_settings
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_text
from django.utils.timezone import activate
from pytz import timezone

from shuup.apps.provides import override_provides
from shuup.core.models import CustomCarrier, FixedCostBehaviorComponent, Order, OrderLine, get_person_contact
from shuup.core.order_creator import OrderCreator
from shuup.default_reports.reports import (
    CustomerSalesReport,
    NewCustomersReport,
    OrderLineReport,
    OrdersReport,
    ProductSalesReport,
    RefundedSalesReport,
    SalesPerHour,
    SalesReport,
    ShippingReport,
    TaxesReport,
    TotalSales,
)
from shuup.reports.admin_module.views import ReportView
from shuup.reports.forms import DateRangeChoices
from shuup.reports.writer import get_writer_instance
from shuup.testing.factories import (
    CompanyFactory,
    OrderLineType,
    UserFactory,
    create_order_with_product,
    create_product,
    create_random_order,
    create_random_person,
    get_address,
    get_default_product,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
    get_initial_order_status,
    get_payment_method,
    get_shop,
    get_test_tax,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.i18n import get_current_babel_locale
from shuup_tests.core.test_basic_order import create_order
from shuup_tests.reports.test_reports import initialize_report_test
from shuup_tests.utils.basketish_order_source import BasketishOrderSource

from .utils import create_orders_for_dates


class InfoTest(object):
    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)


def initialize_simple_report(cls, data_overrides={}):
    product_price = 100
    product_count = 2
    tax_rate = Decimal("0.10")
    line_count = 1
    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(
        product_price, product_count, tax_rate, line_count
    )
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
    return InfoTest(
        **{
            "expected_taxful_total": expected_taxful_total,
            "expected_taxless_total": expected_taxless_total,
            "json_data": json_data,
            "product_count": product_count,
            "shop": shop,
            "writer": writer,
            "report": report,
            "order": order,
        }
    )


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
    assert float(test_info.expected_taxful_total) == return_data.get("total_sales")


@pytest.mark.django_db
def test_orders_report(rf):
    test_info = initialize_simple_report(OrdersReport)
    assert force_text(OrdersReport.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert return_data.get("status") == test_info.order.status.name
    assert return_data.get("order_line_quantity") == int(test_info.order.lines.count())
    assert return_data.get("customer") == test_info.order.get_customer_name()


@pytest.mark.django_db
def test_order_line_report(rf):
    test_info = initialize_simple_report(OrderLineReport, {"order_line_type": [1]})
    assert force_text(OrderLineReport.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert len(test_info.json_data.get("tables")[0].get("columns")) == 8
    assert len(test_info.json_data["tables"][0]["data"]) == OrderLine.objects.filter(type=1).count()

    test_info = initialize_simple_report(OrderLineReport, {"order_line_type": [1, 2]})
    assert force_text(OrderLineReport.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert len(test_info.json_data.get("tables")[0].get("columns")) == 8
    assert len(test_info.json_data["tables"][0]["data"]) == OrderLine.objects.filter(type__in=[1, 2]).count()

    supplier = get_default_supplier()
    test_info = initialize_simple_report(OrderLineReport, {"supplier": [supplier.pk]})
    assert force_text(OrderLineReport.title) in test_info.json_data.get("heading")
    assert len(test_info.json_data["tables"][0]["data"]) == OrderLine.objects.filter(supplier=supplier).count()

    test_info = initialize_simple_report(OrderLineReport, {"order_status": [1]})
    assert force_text(OrderLineReport.title) in test_info.json_data.get("heading")
    assert len(test_info.json_data["tables"][0]["data"]) == OrderLine.objects.filter(order__status__in=[1]).count()


@pytest.mark.django_db
def test_total_sales_customers_report(rf):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    p1 = create_product("p1", shop=shop, supplier=supplier, default_price="5")
    p2 = create_product("p2", shop=shop, supplier=supplier, default_price="20")

    # orders for person 1
    person1 = create_random_person()
    order1 = create_random_order(customer=person1, completion_probability=1, products=[p1, p2])
    order2 = create_random_order(customer=person1, completion_probability=1, products=[p1, p2])

    # orders for person 2
    person2 = create_random_person()
    order3 = create_random_order(customer=person2, completion_probability=1, products=[p1, p2])
    order4 = create_random_order(customer=person2, completion_probability=1, products=[p1, p2])
    order5 = create_random_order(customer=person2, completion_probability=1, products=[p1, p2])

    # pay orders
    [o.create_payment(o.taxful_total_price) for o in Order.objects.all()]

    data = {
        "report": TotalSales.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.ALL_TIME,
        "writer": "json",
        "force_download": 1,
    }
    report = TotalSales(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    assert force_text(TotalSales.title) in json_data.get("heading")
    data = json_data.get("tables")[0].get("data")[0]

    avg_sales = (
        order1.taxful_total_price
        + order2.taxful_total_price
        + order3.taxful_total_price
        + order4.taxful_total_price
        + order5.taxful_total_price
    ) / Decimal(5)

    assert int(data["customers"]) == 2
    assert int(data["order_amount"]) == 5
    assert data["customer_avg_sale"] == float(avg_sales.value.quantize(Decimal("0.01")))


@pytest.mark.django_db
def test_total_sales_report_with_zero_total(rf):
    new_customer = create_random_person()  # This customer shouldn't have any sales
    test_info = initialize_simple_report(TotalSales, data_overrides={"customer": [new_customer]})
    assert force_text(TotalSales.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")[0]
    assert return_data.get("currency") == test_info.shop.currency
    assert return_data.get("name") == test_info.shop.name
    assert int(return_data.get("order_amount")) == 0
    assert float(test_info.shop.create_price(0).as_rounded().value) == return_data.get("total_sales")


@pytest.mark.django_db
def test_total_sales_per_hour_report(rf):
    test_info = initialize_simple_report(SalesPerHour)
    assert force_text(SalesPerHour.title) in test_info.json_data.get("heading")
    return_data = test_info.json_data.get("tables")[0].get("data")
    order_hour = test_info.order.order_date.strftime("%H")

    assert len(return_data) == 24  # all hours present
    assert min([int(data_item.get("hour")) for data_item in return_data]) == 0
    assert max([int(data_item.get("hour")) for data_item in return_data]) == 23
    for hour_data in return_data:
        if int(hour_data.get("hour")) == int(order_hour):
            assert float(test_info.expected_taxful_total) == hour_data.get("total_sales")
        else:
            assert hour_data.get("total_sales") == 0


@pytest.mark.django_db
def test_contact_filters(rf, admin_user):
    shop = get_default_shop()
    products_per_order = 5

    request = rf.get("/")
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
    _assert_expected_values(
        expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data
    )

    # test that new admin user gets one order
    expected_taxful_total_price = order_three.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price
    expected_order_count = 1
    test_info = initialize_simple_report(SalesReport, data_overrides={"creator": [user.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(
        expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data
    )

    # test that new admin user and second_customer gets one order
    expected_taxful_total_price = order_three.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price
    expected_order_count = 1
    test_info = initialize_simple_report(
        SalesReport, data_overrides={"creator": [user.pk], "customer": [second_customer.pk]}
    )
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(
        expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data
    )

    # test that second_customer gets two orders
    expected_taxful_total_price = order_three.taxful_total_price + order_two.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price + order_two.taxless_total_price
    expected_order_count = 2
    test_info = initialize_simple_report(SalesReport, data_overrides={"customer": [second_customer.pk]})
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(
        expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data
    )

    # test that second_customer gets two orders
    expected_taxful_total_price = order_three.taxful_total_price
    expected_taxless_total_price = order_three.taxless_total_price
    expected_order_count = 1
    test_info = initialize_simple_report(
        SalesReport, data_overrides={"customer": [second_customer.pk], "orderer": [customer.pk]}
    )
    return_data = test_info.json_data.get("tables")[0].get("data")
    _assert_expected_values(
        expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data
    )


def _assert_expected_values(
    expected_order_count, expected_taxful_total_price, expected_taxless_total_price, products_per_order, return_data
):
    assert len(return_data) == 1  # only one row since both are on same day
    assert int(return_data[0].get("order_count")) == expected_order_count
    assert int(return_data[0].get("product_count")) == products_per_order * expected_order_count
    assert return_data[0].get("taxful_total") == float(expected_taxful_total_price)
    assert return_data[0].get("taxless_total") == float(expected_taxless_total_price)


@pytest.mark.django_db
@pytest.mark.parametrize("order_by", ["quantity", "taxless_total", "taxful_total"])
def test_product_total_sales_report(rf, admin_user, order_by):
    with override_provides("reports", ["shuup.default_reports.reports.product_total_sales:ProductSalesReport"]):
        shop = get_default_shop()
        supplier = get_default_supplier(shop)
        product1 = create_product("product1", supplier=supplier, shop=shop)
        product2 = create_product("product2", supplier=supplier, shop=shop)

        p1_qtd, p1_price, p1_tr, p1_lines = Decimal(3), Decimal(5), Decimal(0), 5
        p2_qtd, p2_price, p2_tr, p2_lines = Decimal(4), Decimal(5), Decimal(0.95), 3

        order = create_order_with_product(
            product=product1,
            supplier=supplier,
            quantity=p1_qtd,
            taxless_base_unit_price=p1_price,
            tax_rate=p1_tr,
            n_lines=p1_lines,
            shop=shop,
        )
        order.create_payment(order.taxful_total_price.amount)

        order2 = create_order_with_product(
            product=product2,
            supplier=supplier,
            quantity=p2_qtd,
            taxless_base_unit_price=p2_price,
            tax_rate=p2_tr,
            n_lines=p2_lines,
            shop=shop,
        )
        order2.create_payment(order2.taxful_total_price.amount)

        data = {
            "report": ProductSalesReport.get_name(),
            "shop": shop.pk,
            "date_range": DateRangeChoices.ALL_TIME.value,
            "writer": "json",
            "force_download": 1,
            "order_by": order_by,
        }

        view = ReportView.as_view()
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code == 200
        json_data = json.loads(response.content.decode("utf-8"))
        assert force_text(ProductSalesReport.title) in json_data.get("heading")

        data = json_data["tables"][0]["data"]
        assert len(data) == 2

        p1_total_qtd = p1_qtd * p1_lines
        p1_taxless_total = p1_total_qtd * p1_price
        p1_taxful_total = p1_taxless_total * (1 + p1_tr)

        p2_total_qtd = p2_qtd * p2_lines
        p2_taxless_total = p2_total_qtd * p2_price
        p2_taxful_total = p2_taxless_total * (1 + p2_tr)

        if order_by == "quantity":
            p1 = data[0]
            p2 = data[1]

        elif order_by == "taxless_total":
            p1 = data[0]
            p2 = data[1]

        else:  # order_by == "taxful_total":
            p1 = data[1]
            p2 = data[0]

        precision = Decimal("0.1") ** 2

        assert p1["product"] == product1.name
        assert Decimal(p1["quantity"]) == p1_total_qtd
        assert Decimal(p1["taxless_total"]) == p1_taxless_total.quantize(precision)
        assert Decimal(p1["taxful_total"]) == p1_taxful_total.quantize(precision)

        assert p2["product"] == product2.name
        assert Decimal(p2["quantity"]) == p2_total_qtd
        assert Decimal(p2["taxless_total"]) == p2_taxless_total.quantize(precision)
        assert Decimal(p2["taxful_total"]) == p2_taxful_total.quantize(precision)


@pytest.mark.django_db
@pytest.mark.parametrize("group_by", ["%Y", "%Y-%m", "%Y-%m-%d"])
def test_new_customers_report(rf, admin_user, group_by):
    with override_provides("reports", ["shuup.default_reports.reports.new_customers:NewCustomersReport"]):
        shop = get_default_shop()

        person_creation_dates = [
            datetime(2015, 1, 2),
            datetime(2015, 1, 1),
            datetime(2016, 2, 2),
        ]
        # create person with NO user
        for creation_date in person_creation_dates:
            person = create_random_person()
            person.created_on = creation_date
            person.save()

        user_person_creation_dates = [
            datetime(2015, 3, 3),
            datetime(2015, 3, 3),
            datetime(2015, 4, 4),
            datetime(2016, 5, 5),
            datetime(2016, 6, 6),
            datetime(2016, 7, 7),
        ]
        # create person with users
        for creation_date in user_person_creation_dates:
            person = create_random_person()
            person.user = UserFactory()
            person.created_on = creation_date
            person.save()

        company_creation_dates = [
            datetime(2015, 1, 1),
            datetime(2015, 8, 8),
            datetime(2015, 9, 9),
        ]
        # create company contacts
        for creation_date in company_creation_dates:
            company = CompanyFactory()
            company.created_on = creation_date
            company.save()

        data = {
            "report": NewCustomersReport.get_name(),
            "shop": shop.pk,
            "date_range": DateRangeChoices.ALL_TIME.value,
            "writer": "json",
            "force_download": 1,
            "group_by": group_by,
        }

        view = ReportView.as_view()
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code == 200
        json_data = json.loads(response.content.decode("utf-8"))
        assert force_text(NewCustomersReport.title) in json_data.get("heading")

        data = json_data["tables"][0]["data"]

        if group_by == "%Y":
            assert len(data) == 3

            assert data[0]["date"] == "2015"
            assert int(data[0]["personcontact"]) == 5
            assert int(data[0]["companycontact"]) == 3
            assert int(data[0]["users"]) == 3

            assert data[1]["date"] == "2016"
            assert int(data[1]["personcontact"]) == 4
            assert int(data[1]["companycontact"]) == 0
            assert int(data[1]["users"]) == 3

        elif group_by == "%Y-%m":
            assert len(data) == 10

            assert data[0]["date"] == "2015-01"
            assert int(data[0]["personcontact"]) == 2
            assert int(data[0]["companycontact"]) == 1
            assert int(data[0]["users"]) == 0

            assert data[1]["date"] == "2015-03"
            assert int(data[1]["personcontact"]) == 2
            assert int(data[1]["companycontact"]) == 0
            assert int(data[1]["users"]) == 2

            assert data[2]["date"] == "2015-04"
            assert int(data[2]["personcontact"]) == 1
            assert int(data[2]["companycontact"]) == 0
            assert int(data[2]["users"]) == 1

            assert data[3]["date"] == "2015-08"
            assert int(data[3]["personcontact"]) == 0
            assert int(data[3]["companycontact"]) == 1
            assert int(data[3]["users"]) == 0

            assert data[4]["date"] == "2015-09"
            assert int(data[4]["personcontact"]) == 0
            assert int(data[4]["companycontact"]) == 1
            assert int(data[4]["users"]) == 0

            assert data[5]["date"] == "2016-02"
            assert int(data[5]["personcontact"]) == 1
            assert int(data[5]["companycontact"]) == 0
            assert int(data[5]["users"]) == 0

            assert data[6]["date"] == "2016-05"
            assert int(data[6]["personcontact"]) == 1
            assert int(data[6]["companycontact"]) == 0
            assert int(data[6]["users"]) == 1

            assert data[7]["date"] == "2016-06"
            assert int(data[7]["personcontact"]) == 1
            assert int(data[7]["companycontact"]) == 0
            assert int(data[7]["users"]) == 1

            assert data[8]["date"] == "2016-07"
            assert int(data[8]["personcontact"]) == 1
            assert int(data[8]["companycontact"]) == 0
            assert int(data[8]["users"]) == 1

        elif group_by == "%Y-%m-%d":
            assert len(data) == 11

            assert data[0]["date"] == "2015-01-01"
            assert int(data[0]["personcontact"]) == 1
            assert int(data[0]["companycontact"]) == 1
            assert int(data[0]["users"]) == 0

            assert data[1]["date"] == "2015-01-02"
            assert int(data[1]["personcontact"]) == 1
            assert int(data[1]["companycontact"]) == 0
            assert int(data[1]["users"]) == 0

            assert data[2]["date"] == "2015-03-03"
            assert int(data[2]["personcontact"]) == 2
            assert int(data[2]["companycontact"]) == 0
            assert int(data[2]["users"]) == 2

            assert data[3]["date"] == "2015-04-04"
            assert int(data[3]["personcontact"]) == 1
            assert int(data[3]["companycontact"]) == 0
            assert int(data[3]["users"]) == 1

            assert data[4]["date"] == "2015-08-08"
            assert int(data[4]["personcontact"]) == 0
            assert int(data[4]["companycontact"]) == 1
            assert int(data[4]["users"]) == 0

            assert data[5]["date"] == "2015-09-09"
            assert int(data[5]["personcontact"]) == 0
            assert int(data[5]["companycontact"]) == 1
            assert int(data[5]["users"]) == 0

            assert data[6]["date"] == "2016-02-02"
            assert int(data[6]["personcontact"]) == 1
            assert int(data[6]["companycontact"]) == 0
            assert int(data[6]["users"]) == 0

            assert data[7]["date"] == "2016-05-05"
            assert int(data[7]["personcontact"]) == 1
            assert int(data[7]["companycontact"]) == 0
            assert int(data[7]["users"]) == 1

            assert data[8]["date"] == "2016-06-06"
            assert int(data[8]["personcontact"]) == 1
            assert int(data[8]["companycontact"]) == 0
            assert int(data[8]["users"]) == 1

            assert data[9]["date"] == "2016-07-07"
            assert int(data[9]["personcontact"]) == 1
            assert int(data[9]["companycontact"]) == 0
            assert int(data[9]["users"]) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("order_by", ["order_count", "average_sales", "taxless_total", "taxful_total"])
def test_customer_sales_report(rf, order_by):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    product1 = create_product("p1", shop=shop, supplier=supplier)
    product2 = create_product("p2", shop=shop, supplier=supplier)
    product3 = create_product("p3", shop=shop, supplier=supplier)
    tax_rate = Decimal("0.3")

    # orders for person 1
    person1 = create_random_person()
    order1 = create_order_with_product(
        product=product1,
        supplier=supplier,
        quantity=2,
        taxless_base_unit_price="5",
        tax_rate=tax_rate,
        n_lines=1,
        shop=shop,
    )
    order1.customer = person1
    order1.save()
    order2 = create_order_with_product(
        product=product2, supplier=supplier, quantity=1, taxless_base_unit_price="10", n_lines=1, shop=shop
    )
    order2.customer = person1
    order2.save()

    person1_taxful_total_sales = order1.taxful_total_price + order2.taxful_total_price
    person1_taxless_total_sales = order1.taxless_total_price + order2.taxless_total_price
    person1_avg_sales = person1_taxful_total_sales / Decimal(2.0)

    # orders for person 2
    person2 = create_random_person()
    order3 = create_order_with_product(
        product=product1,
        supplier=supplier,
        quantity=2,
        taxless_base_unit_price="5",
        tax_rate=tax_rate,
        n_lines=1,
        shop=shop,
    )
    order3.customer = person2
    order3.save()

    order4 = create_order_with_product(
        product=product2, supplier=supplier, quantity=2, taxless_base_unit_price="50", n_lines=1, shop=shop
    )
    order4.customer = person2
    order4.save()

    order5 = create_order_with_product(
        product=product3,
        supplier=supplier,
        quantity=2,
        taxless_base_unit_price="20",
        tax_rate=tax_rate,
        n_lines=1,
        shop=shop,
    )
    order5.customer = person2
    order5.save()
    person2_taxful_total_sales = order3.taxful_total_price + order4.taxful_total_price + order5.taxful_total_price
    person2_taxless_total_sales = order3.taxless_total_price + order4.taxless_total_price + order5.taxless_total_price
    person2_avg_sales = (person2_taxful_total_sales / Decimal(3.0)).quantize(Decimal("0.01"))

    # pay orders
    [o.create_payment(o.taxful_total_price) for o in Order.objects.all()]

    data = {
        "report": CustomerSalesReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.ALL_TIME,
        "writer": "json",
        "force_download": 1,
        "order_by": order_by,
    }
    report = CustomerSalesReport(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    assert force_text(CustomerSalesReport.title) in json_data.get("heading")
    data = json_data.get("tables")[0].get("data")

    assert len(data) == 2

    if order_by == "order_count":
        person1_data = data[1]
        person2_data = data[0]

    elif order_by == "average_sales":
        if person1_avg_sales > person2_avg_sales:
            person1_data = data[0]
            person2_data = data[1]
        else:
            person1_data = data[1]
            person2_data = data[0]

    elif order_by == "taxless_total":
        if person1_taxless_total_sales > person2_taxless_total_sales:
            person1_data = data[0]
            person2_data = data[1]
        else:
            person1_data = data[1]
            person2_data = data[0]

    elif order_by == "taxful_total":
        if person1_taxful_total_sales > person2_taxful_total_sales:
            person1_data = data[0]
            person2_data = data[1]
        else:
            person1_data = data[1]
            person2_data = data[0]

    assert person1_data["customer"] == person1.name
    assert person1_data["order_count"] == 2
    assert person1_data["average_sales"] == float(person1_avg_sales.value)
    assert person1_data["taxless_total"] == float(person1_taxless_total_sales.value.quantize(Decimal("0.01")))
    assert person1_data["taxful_total"] == float(person1_taxful_total_sales.value.quantize(Decimal("0.01")))

    assert person2_data["customer"] == person2.name
    assert person2_data["order_count"] == 3
    assert person2_data["average_sales"] == float(person2_avg_sales.value)
    assert person2_data["taxless_total"] == float(person2_taxless_total_sales.value.quantize(Decimal("0.01")))
    assert person2_data["taxful_total"] == float(person2_taxful_total_sales.value.quantize(Decimal("0.01")))


@pytest.mark.django_db
def test_taxes_report(rf):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    product1 = create_product("p1", shop=shop, supplier=supplier)
    product2 = create_product("p2", shop=shop, supplier=supplier)
    create_product("p3", shop=shop, supplier=supplier)
    tax_rate1 = Decimal("0.3")
    tax_rate2 = Decimal("0.45")

    tax_rate1_instance = get_test_tax(tax_rate1)
    tax_rate2_instance = get_test_tax(tax_rate2)

    # orders for person 1
    person1 = create_random_person()
    order1 = create_order_with_product(
        product=product1,
        supplier=supplier,
        quantity=2,
        taxless_base_unit_price="5",
        tax_rate=tax_rate1,
        n_lines=1,
        shop=shop,
    )
    order1.customer = person1
    order1.save()
    order2 = create_order_with_product(
        product=product2,
        supplier=supplier,
        quantity=1,
        taxless_base_unit_price="10",
        tax_rate=tax_rate1,
        n_lines=1,
        shop=shop,
    )
    order2.customer = person1
    order2.save()

    # orders for person 2
    person2 = create_random_person()
    order3 = create_order_with_product(
        product=product1,
        supplier=supplier,
        quantity=1,
        taxless_base_unit_price="2",
        tax_rate=tax_rate2,
        n_lines=1,
        shop=shop,
    )
    order3.customer = person2
    order3.save()

    order4 = create_order_with_product(
        product=product2,
        supplier=supplier,
        quantity=2,
        taxless_base_unit_price="8",
        tax_rate=tax_rate1,
        n_lines=1,
        shop=shop,
    )
    order4.customer = person2
    order4.save()

    # pay orders
    [o.create_payment(o.taxful_total_price) for o in Order.objects.all()]

    data = {
        "report": TaxesReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.ALL_TIME,
        "writer": "json",
        "force_download": 1,
    }
    report = TaxesReport(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    assert force_text(TaxesReport.title) in json_data.get("heading")
    data = json_data.get("tables")[0].get("data")
    assert len(data) == 2

    tax1_rate1_total = (
        (order1.taxful_total_price_value - order1.taxless_total_price_value)
        + (order2.taxful_total_price_value - order2.taxless_total_price_value)
        + (order4.taxful_total_price_value - order4.taxless_total_price_value)
    )
    tax1_pretax_total = (
        order1.taxless_total_price_value + order2.taxless_total_price_value + order4.taxless_total_price_value
    )
    tax1_total = order1.taxful_total_price_value + order2.taxful_total_price_value + order4.taxful_total_price_value
    tax2_rate2_total = order3.taxful_total_price_value - order3.taxless_total_price_value

    # the report data order is the total charged ascending
    expected_result = [
        {
            "tax": tax_rate2_instance.name,
            "tax_rate": tax_rate2,
            "order_count": 1,
            "total_pretax_amount": order3.taxless_total_price_value,
            "total_tax_amount": tax2_rate2_total,
            "total": order3.taxful_total_price_value,
        },
        {
            "tax": tax_rate1_instance.name,
            "tax_rate": tax_rate1,
            "order_count": 3,
            "total_pretax_amount": tax1_pretax_total,
            "total_tax_amount": tax1_rate1_total,
            "total": tax1_total,
        },
    ]
    for ix, tax in enumerate(data):
        assert tax["tax"] == expected_result[ix]["tax"]
        assert Decimal(tax["tax_rate"]) == expected_result[ix]["tax_rate"] * Decimal(100.0)
        assert tax["order_count"] == float(expected_result[ix]["order_count"])
        assert tax["total_tax_amount"] == float(expected_result[ix]["total_tax_amount"])
        assert tax["total_pretax_amount"] == float(expected_result[ix]["total_pretax_amount"])
        assert tax["total"] == float(expected_result[ix]["total"])


def seed_source(shipping_method=None, produce_price=10, shop=None):
    if not shop:
        shop = get_default_shop()
    source = BasketishOrderSource(shop)
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge")
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = create_random_person()
    source.payment_method = get_payment_method(shop=shop)
    source.shipping_method = shipping_method if shipping_method else get_default_shipping_method()
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(shop),
        quantity=1,
        base_unit_price=source.create_price(produce_price),
    )
    return source


@pytest.mark.parametrize("prices_include_tax", (False, True))
@pytest.mark.django_db
def test_shipping_report(rf, prices_include_tax):
    shop = get_shop(prices_include_tax=prices_include_tax)
    tax_class = get_default_tax_class()
    creator = OrderCreator()

    carrier1 = CustomCarrier.objects.create(name="Carrier1")
    sm1 = carrier1.create_service(None, shop=shop, enabled=True, tax_class=tax_class, name="SM #1")
    sm1.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=Decimal(10)))
    sm2 = carrier1.create_service(None, shop=shop, enabled=True, tax_class=tax_class, name="SM #2")
    sm2.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=Decimal(99)))
    sm2.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=Decimal(4)))

    carrier2 = CustomCarrier.objects.create(name="Carrier2")
    sm3 = carrier2.create_service(None, shop=shop, enabled=True, tax_class=tax_class, name="SM #3")
    sm3.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=Decimal(5)))

    source1 = seed_source(sm1, shop=shop)
    source2 = seed_source(sm1, shop=shop)
    source3 = seed_source(sm2, shop=shop)
    source4 = seed_source(sm3, shop=shop)

    creator.create_order(source1)
    creator.create_order(source2)
    creator.create_order(source3)
    creator.create_order(source4)

    # pay orders
    [o.create_payment(o.taxful_total_price) for o in Order.objects.all()]

    data = {
        "report": ShippingReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.ALL_TIME,
        "writer": "json",
        "force_download": 1,
    }
    report = ShippingReport(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    assert force_text(ShippingReport.title) in json_data.get("heading")
    data = json_data.get("tables")[0].get("data")
    assert len(data) == 3

    expected_result = [
        {
            "carrier": carrier1.name,
            "shipping_method": sm1.name,
            "order_count": 2,
            "total_charged": sum([bc.price_value for bc in sm1.behavior_components.all()]) * 2,  # 2 orders
        },
        {
            "carrier": carrier1.name,
            "shipping_method": sm2.name,
            "order_count": 1,
            "total_charged": sum([bc.price_value for bc in sm2.behavior_components.all()]),
        },
        {
            "carrier": carrier2.name,
            "shipping_method": sm3.name,
            "order_count": 1,
            "total_charged": sum([bc.price_value for bc in sm3.behavior_components.all()]),
        },
    ]

    for ix, shipping in enumerate(data):
        assert shipping["carrier"] == expected_result[ix]["carrier"]
        assert shipping["shipping_method"] == expected_result[ix]["shipping_method"]
        assert shipping["order_count"] == int(expected_result[ix]["order_count"])
        assert shipping["total_charged"] == float(expected_result[ix]["total_charged"].quantize(Decimal("0.01")))


@pytest.mark.django_db
def test_refunds_report(rf):
    shop = get_default_shop()
    get_default_tax_class()
    creator = OrderCreator()

    source1 = seed_source()
    source2 = seed_source()
    source3 = seed_source()
    source4 = seed_source()

    order1 = creator.create_order(source1)
    order2 = creator.create_order(source2)
    order3 = creator.create_order(source3)
    order4 = creator.create_order(source4)

    # pay orders
    [o.create_payment(o.taxful_total_price) for o in Order.objects.all()]

    order1.create_full_refund()
    order2.create_refund(
        [{"line": order2.lines.first(), "amount": order2.taxful_total_price.amount * Decimal(0.5), "quantity": 1}]
    )
    order3.create_refund(
        [{"line": order3.lines.first(), "amount": order3.taxful_total_price.amount * Decimal(0.3), "quantity": 1}]
    )
    order4.create_refund(
        [{"line": order4.lines.first(), "amount": order4.taxful_total_price.amount * Decimal(0.1), "quantity": 1}]
    )

    total_refunded = (
        order1.get_total_refunded_amount()
        + order2.get_total_refunded_amount()
        + order3.get_total_refunded_amount()
        + order4.get_total_refunded_amount()
    )

    data = {
        "report": RefundedSalesReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.ALL_TIME,
        "writer": "json",
        "force_download": 1,
    }
    report = RefundedSalesReport(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    assert force_text(RefundedSalesReport.title) in json_data.get("heading")
    data = json_data.get("tables")[0].get("data")
    assert len(data) == 1
    data = data[0]

    expected_data = {"refunded_orders": 4, "total_refunded": float(total_refunded.value)}

    for k, v in expected_data.items():
        assert data[k] == v


@pytest.mark.parametrize("server_timezone", ["America/Los_Angeles", "America/Sao_Paulo"])
@pytest.mark.django_db
def test_sales_report_timezone(server_timezone):
    with override_settings(TIME_ZONE=server_timezone):
        # Timezone needs to be activated to current one because some old timezone can still be active
        activate(pytz.timezone(server_timezone))
        """
        TIME TABLE

        | identifier  | ISO 8859-1                | UTC                 | America/Los_Angeles | America/Sao_Paulo   |
        | first_date  | 2017-10-01T23:50:00+03:00 | 2017-10-01 20:50:00 | 2017-10-01 13:50:00 | 2017-10-01 17:50:00 |
        | second_date | 2017-10-02T17:13:00+10:00 | 2017-10-02 07:13:00 | 2017-10-02 00:13:00 | 2017-10-02 04:13:00 |
        | third_date  | 2017-10-02T22:04:44-01:00 | 2017-10-02 23:04:44 | 2017-10-02 16:04:44 | 2017-10-02 20:04:44 |
        | forth_date  | 2017-10-02T23:04:44-05:00 | 2017-10-03 04:04:44 | 2017-10-02 21:04:44 | 2017-10-03 01:04:44 |
        """

        first_date = parse_datetime("2017-10-01T23:50:00+03:00")
        second_date = parse_datetime("2017-10-02T17:13:00+10:00")
        third_date = parse_datetime("2017-10-02T22:04:44-01:00")
        forth_date = parse_datetime("2017-10-02T23:04:44-05:00")

        inited_data = create_orders_for_dates([first_date, second_date, third_date, forth_date], as_paid=True)
        assert Order.objects.count() == 4

        first_date_local = first_date.astimezone(timezone(server_timezone))
        second_date_local = second_date.astimezone(timezone(server_timezone))
        third_date_local = third_date.astimezone(timezone(server_timezone))
        forth_date_local = forth_date.astimezone(timezone(server_timezone))

        data = {
            "report": SalesReport.get_name(),
            "shop": inited_data["shop"].pk,
            "start_date": first_date_local,
            "end_date": second_date_local,
        }
        report = SalesReport(**data)
        report_data = report.get_data()["data"]
        assert len(report_data) == 2

        # the orders should be rendered as localtime
        assert report_data[0]["date"] == format_date(second_date_local, locale=get_current_babel_locale())
        assert report_data[1]["date"] == format_date(first_date_local, locale=get_current_babel_locale())

        # includes the 3rd order
        data.update({"start_date": first_date_local, "end_date": third_date_local})
        report = SalesReport(**data)
        report_data = report.get_data()["data"]
        assert len(report_data) == 2

        assert report_data[0]["date"] == format_date(second_date_local, locale=get_current_babel_locale())
        assert report_data[1]["date"] == format_date(first_date_local, locale=get_current_babel_locale())

        # includes the 4th order - here the result is different for Los_Angeles and Sao_Paulo
        data.update({"start_date": first_date_local, "end_date": forth_date_local})
        report = SalesReport(**data)
        report_data = report.get_data()["data"]

        if server_timezone == "America/Los_Angeles":
            assert len(report_data) == 2
            assert report_data[0]["date"] == format_date(second_date_local, locale=get_current_babel_locale())
            assert report_data[1]["date"] == format_date(first_date_local, locale=get_current_babel_locale())
        else:
            assert len(report_data) == 3
            assert report_data[0]["date"] == format_date(forth_date_local, locale=get_current_babel_locale())
            assert report_data[1]["date"] == format_date(second_date_local, locale=get_current_babel_locale())
            assert report_data[2]["date"] == format_date(first_date_local, locale=get_current_babel_locale())

        # Using strings as start or end date should raise TypeError.
        # Only date or datetime objects should be accepted.
        data.update({"start_date": first_date_local.isoformat(), "end_date": forth_date_local.isoformat()})
        with pytest.raises(TypeError):
            report = SalesReport(**data)
            report_data = report.get_data()["data"]

        # Using different date types in start and end date should raise TypeError.
        data.update({"start_date": first_date_local, "end_date": forth_date_local.date()})
        with pytest.raises(TypeError):
            report = SalesReport(**data)
            report_data = report.get_data()["data"]


@pytest.mark.parametrize("server_timezone", ["America/Los_Angeles", "America/Sao_Paulo"])
@pytest.mark.django_db
def test_sales_report_per_hour_timezone(server_timezone):
    with override_settings(TIME_ZONE=server_timezone):
        # Timezone needs to be activated to current one because some old timezone can still be active
        activate(pytz.timezone(server_timezone))
        """
        TIME TABLE

        | identifier  | ISO 8859-1                | UTC                 | America/Los_Angeles | America/Sao_Paulo   |
        | first_date  | 2017-10-01T23:50:00+03:00 | 2017-10-01 20:50:00 | 2017-10-01 13:50:00 | 2017-10-01 17:50:00 |
        | second_date | 2017-10-02T17:13:00+10:00 | 2017-10-02 07:13:00 | 2017-10-02 00:13:00 | 2017-10-02 04:13:00 |
        | third_date  | 2017-10-02T22:04:44-01:00 | 2017-10-02 23:04:44 | 2017-10-02 16:04:44 | 2017-10-02 20:04:44 |
        | forth_date  | 2017-10-02T23:04:44-05:00 | 2017-10-03 04:04:44 | 2017-10-02 21:04:44 | 2017-10-03 01:04:44 |
        """

        first_date = parse_datetime("2017-10-01T23:50:00+03:00")
        second_date = parse_datetime("2017-10-02T17:13:00+10:00")
        third_date = parse_datetime("2017-10-02T22:04:44-01:00")
        forth_date = parse_datetime("2017-10-02T23:04:44-05:00")

        inited_data = create_orders_for_dates([first_date, second_date, third_date, forth_date], as_paid=True)
        assert Order.objects.count() == 4

        first_date_local = first_date.astimezone(timezone(server_timezone))
        second_date_local = second_date.astimezone(timezone(server_timezone))
        third_date_local = third_date.astimezone(timezone(server_timezone))
        forth_date_local = forth_date.astimezone(timezone(server_timezone))

        data = {
            "report": SalesPerHour.get_name(),
            "shop": inited_data["shop"].pk,
            "start_date": first_date_local,
            "end_date": forth_date_local,
        }
        report = SalesPerHour(**data)
        report_data = report.get_data()["data"]

        if server_timezone == "America/Los_Angeles":
            # should have orders in hours: 00, 13, 16 and 21
            expected_hours = [0, 13, 16, 21]
            for hour in range(24):
                if hour in expected_hours:
                    assert report_data[hour]["order_amount"] == 1
                else:
                    assert report_data[hour]["order_amount"] == 0
        else:
            # should have orders in hours: 01, 04, 17 and 20
            expected_hours = [1, 4, 17, 20]
            for hour in range(24):
                if hour in expected_hours:
                    assert report_data[hour]["order_amount"] == 1
                else:
                    assert report_data[hour]["order_amount"] == 0
