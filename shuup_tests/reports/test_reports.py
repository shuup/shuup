# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import itertools
import json
from datetime import date
from decimal import Decimal

import pytest
import six
from babel.dates import format_date
from bs4 import BeautifulSoup
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.safestring import SafeText
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import override_provides
from shuup.core.order_creator import OrderCreator

from shuup.core.models import Order, AnonymousContact, OrderLineType, ShippingStatus, FixedCostBehaviorComponent
from shuup.core.pricing import TaxfulPrice, TaxlessPrice, get_pricing_module
from shuup.reports.admin_module.views import ReportView
from shuup.reports.forms import DateRangeChoices
from shuup.reports.report import ShuupReportBase
from shuup.reports.writer import (
    ExcelReportWriter, get_writer_instance, HTMLReportWriter, JSONReportWriter,
    PDFReportWriter, PprintReportWriter, REPORT_WRITERS_MAP,
    ReportWriterPopulator
)
from shuup.testing.factories import (
    create_order_with_product, get_default_product, get_default_shop,
    get_default_supplier, get_default_shipping_method, create_empty_order, add_product_to_order, get_shop,
    get_initial_order_status, create_product, get_default_tax_class, get_default_category, get_address,
    get_shipping_method
)
from shuup.default_reports.reports import ShippingReport
from shuup.testing.utils import apply_request_middleware
from shuup_tests.simple_supplier.utils import get_simple_supplier
from shuup_tests.utils.basketish_order_source import BasketishOrderSource
from shuup.utils.i18n import get_current_babel_locale
from shuup.utils.money import Money


def initialize_report_test(product_price, product_count, tax_rate, line_count):
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    expected_taxless_total = product_count * product_price
    expected_taxful_total = product_count * product_price * (1 + tax_rate)
    order = create_order_with_product(
        product=product, supplier=supplier, quantity=product_count,
        taxless_base_unit_price=product_price, tax_rate=tax_rate, n_lines=line_count, shop=shop)
    order.create_payment(order.taxful_total_price.amount)
    order2 = create_order_with_product(
        product=product, supplier=supplier, quantity=product_count,
        taxless_base_unit_price=product_price, tax_rate=tax_rate, n_lines=line_count, shop=shop)
    order2.create_payment(order2.taxful_total_price.amount)
    order2.set_canceled()  # Shouldn't affect reports
    return expected_taxful_total, expected_taxless_total, shop, order


def _get_product_data(identifier="0"):
    return [
        {
            "sku": "sku1" + identifier,
            "default_price": Decimal("14.756"),
            "quantity": Decimal("2")
        },
        {
            "sku": "sku2" + identifier,
            "default_price": Decimal("10"),
            "quantity": Decimal("2")
        },
        {
            "sku": "sku3" + identifier,
            "default_price": Decimal("14.756"),
            "quantity": Decimal("2")
        }
    ]

def _get_order(prices_include_tax=False, include_basket_campaign=False, include_catalog_campaign=False, identifier="0"):
    shop = get_default_shop()
    shop.prices_include_tax = prices_include_tax
    shop.save()
    supplier = get_simple_supplier()
    source = BasketishOrderSource(shop)
    sm = get_shipping_method(shop = shop, name="PostExpressRS", price=100)
    sm.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=10))
    sm.save()
    source.shipping_method = sm
    source.status = get_initial_order_status()
    ctx = get_pricing_module().get_context_from_data(shop, AnonymousContact())
    products = []
    for product_data in _get_product_data(identifier):
        quantity = product_data.pop("quantity")
        product = create_product(
            sku=product_data.pop("sku"),
            shop=shop,
            supplier=supplier,
            tax_class=get_default_tax_class(),
            **product_data)
        shop_product = product.get_shop_instance(shop)
        shop_product.categories.add(get_default_category())
        shop_product.save()
        supplier.adjust_stock(product.id, 10)
        pi = product.get_price_info(ctx)
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=product,
            supplier=supplier,
            quantity=quantity,
            base_unit_price=pi.base_unit_price,
            discount_amount=pi.discount_amount
        )
        products.append(product)
    oc = OrderCreator()
    order = oc.create_order(source)
    return order, products

class SalesTestReport(ShuupReportBase):
    identifier = "test_sales_report"
    title = _("Sales Report")

    filename_template = "sales-report-%(time)s"
    schema = [
        {"key": "date", "title": _("Date")},
        {"key": "order_count", "title": _("Orders")},
        {"key": "product_count", "title": _("Products")},
        {"key": "taxless_total", "title": _("Taxless Total")},
        {"key": "taxful_total", "title": _("Taxful Total")},
    ]

    def get_objects(self):
        return Order.objects.filter(
            shop=self.shop, order_date__range=(self.start_date, self.end_date)).valid().paid().order_by("order_date")

    def extract_date(self, entity):
        # extracts the starting date from an entity
        return entity.order_date.date()

    def get_data(self):
        orders = self.get_objects().order_by("-order_date")
        data = []
        for order_date, orders_group in itertools.groupby(orders, key=self.extract_date):
            taxless_total = TaxlessPrice(0, currency=self.shop.currency)
            taxful_total = TaxfulPrice(0, currency=self.shop.currency)
            paid_total = TaxfulPrice(0, currency=self.shop.currency)
            product_count = 0
            order_count = 0
            for order in orders_group:
                taxless_total += order.taxless_total_price
                taxful_total += order.taxful_total_price
                product_count += sum(order.get_product_ids_and_quantities().values())
                order_count += 1
                if order.payment_date:
                    paid_total += order.taxful_total_price

            data.append({
                "date": format_date(order_date, format="short", locale=get_current_babel_locale()),
                "order_count": order_count,
                "product_count": int(product_count),
                "taxless_total": taxless_total,
                "taxful_total": taxful_total,
            })

        return self.get_return_data(data)


class SalesTestReportForRequestTest(SalesTestReport):
    def get_objects(self):
        assert self.request
        return super(SalesTestReportForRequestTest, self).get_objects()

    def get_data(self):
        assert self.request
        return super(SalesTestReportForRequestTest, self).get_data()


@pytest.mark.django_db
def test_reporting(rf, admin_user):

    product_price = 100
    product_count = 2
    tax_rate = Decimal("0.10")
    line_count = 1

    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(product_price,
                                                                                        product_count,
                                                                                        tax_rate,
                                                                                        line_count)

    with override_provides("reports", [__name__ + ":SalesTestReportForRequestTest"]):
        data = {
            "report": SalesTestReport.get_name(),
            "shop": shop.pk,
            "date_range": DateRangeChoices.THIS_YEAR.value,
            "writer": "json",
            "force_download": 1,
        }

        view = ReportView.as_view()
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code == 200
        json_data = json.loads(response.content.decode("utf-8"))
        assert force_text(SalesTestReport.title) in json_data.get("heading")
        totals = json_data.get("tables")[0].get("totals")
        return_data = json_data.get("tables")[0].get("data")[0]
        assert int(totals.get("product_count", 0)) == product_count
        assert int(return_data.get("product_count", 0)) == product_count
        assert int(totals.get("order_count", 0)) == 1
        assert int(return_data.get("order_count", 0)) == 1
        assert str(expected_taxless_total) in totals.get("taxless_total", "0")
        assert str(expected_taxful_total) in totals.get("taxful_total", "0")

        today = date.today()
        last_year = date(today.year - 1, 1, 1)
        next_year = date(today.year + 1, 1, 1)

        # test report without downloading it
        data = {
            "report": SalesTestReport.get_name(),
            "shop": shop.pk,
            "date_range": DateRangeChoices.CUSTOM.value,
            "start_date": last_year.strftime("%Y-%m-%d"),
            "end_date": next_year.strftime("%Y-%m-%d"),
            "writer": "json",
        }

        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request)
        assert response.status_code == 200

        soup = BeautifulSoup(response.render().content)
        response_text = str(six.u(soup.encode('ascii')))
        assert force_text(SalesTestReport.title) in response_text
        assert str(expected_taxless_total) in response_text
        assert str(expected_taxful_total) in response_text


@pytest.mark.django_db
def test_html_writer(rf):
    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(10, 1, 0, 1)
    data = {
        "report": SalesTestReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "html",
        "force_download": 1,
    }
    report = SalesTestReport(**data)
    writer = get_writer_instance(data["writer"])
    assert str(writer) == data["writer"]
    rendered_report = writer.render_report(report=report)

    soup = BeautifulSoup(rendered_report)
    assert force_text(SalesTestReport.title) in str(soup)
    assert str(expected_taxless_total) in str(soup)
    assert str(expected_taxful_total) in str(soup)

    rendered_report = writer.render_report(report=report, inline=True)
    assert type(rendered_report) == SafeText
    assert force_text(SalesTestReport.title) in rendered_report
    assert str(expected_taxless_total) in rendered_report
    assert str(expected_taxful_total) in rendered_report


@pytest.mark.django_db
def test_excel_writer(rf):
    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(10, 1, 0, 1)
    data = {
        "report": SalesTestReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "excel",
        "force_download": 1,
    }
    report = SalesTestReport(**data)
    writer = get_writer_instance(data["writer"])
    assert str(writer) == data["writer"]
    rendered_report = writer.get_rendered_output()
    assert rendered_report is not None


def test_report_writer_populator_provide():
    with override_provides("report_writer_populator", [
        "shuup.reports.writer.populate_default_writers"
    ]):
        populator = ReportWriterPopulator()
        populator.populate()

        for k, v in REPORT_WRITERS_MAP.items():
            assert populator.populated_map[k] == v


def test_report_writers():
    """
    Just check whether something breaks while writing differnt types of data
    """
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    order = create_order_with_product(
        product=product, supplier=supplier, quantity=1, taxless_base_unit_price=10, tax_rate=0, n_lines=2, shop=shop)
    order.create_payment(order.taxful_total_price.amount)

    data = {
        "report": SalesTestReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "html",
        "force_download": 1,
    }
    report = SalesTestReport(**data)

    for writer_cls in [ExcelReportWriter, PDFReportWriter, PprintReportWriter, HTMLReportWriter, JSONReportWriter]:
        writer = writer_cls()
        report_data = [
            {
                "date": order,
                "order_count": Decimal(2),
                "product_count": int(3),
                "taxless_total": lazy(lambda: order.taxless_total_price_value),
                "taxful_total": order.taxful_total_price,
            }
        ]
        writer.write_data_table(report, report_data)
        assert writer.get_rendered_output()


def test_get_totals_return_correct_totals():
    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(10, 1, 0, 1)
    report_data = {
        "report": SalesTestReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "html",
        "force_download": 1,
    }
    data = [{
        "date": "",
        "order_count": None,
        "product_count": 10,
        "taxless_total": TaxlessPrice("10", "EUR"),
        "taxful_total": TaxfulPrice("5", "EUR"),
    }, {
        "date": "",
        "order_count": 12,
        "product_count": None,
        "taxless_total": TaxlessPrice("20", "EUR"),
        "taxful_total": None,
    }]
    report = SalesTestReport(**report_data)
    totals = report.get_totals(data)
    expected = {
        "date": None,
        "order_count": 12,
        "product_count": 10,
        "taxless_total": TaxlessPrice("30", "EUR"),
        "taxful_total": TaxfulPrice("5", "EUR")
    }
    assert totals == expected


@pytest.mark.parametrize("start_date,end_date", [
    (None, None),
    ("1990-01-01", None),
    (None, "2100-01-01")
])
@pytest.mark.django_db
def test_none_dates(start_date, end_date):
    _, _, shop, order = initialize_report_test(10, 2, 0, 1)

    for timezone in ["UTC", "America/Sao_Paulo", "Etc/GMT+12", "Pacific/Kiritimati"]:
        with override_settings(TIME_ZONE=timezone):
            data = {
                "report": SalesTestReport.get_name(),
                "shop": shop.pk,
                "start_date": start_date,
                "end_date": end_date,
                "writer": "json",
                "force_download": 1
            }
            report = SalesTestReport(**data)
            data = report.get_data()
            assert data["data"]


@pytest.mark.django_db
def test_shipping_report():
    supplier = get_simple_supplier()
    order, products = _get_order(False, True, True)
    shipping_address = get_address(name="Shippy Doge").to_immutable()
    shipping_address.save()
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    order.shipping_address = shipping_address

    total_charged = Money(0, 'EUR')

    order.create_payment(order.get_total_unpaid_amount())
    order.save()
    assert order.shipping_address
    order.create_shipment({x : Decimal("2") for x in products}, supplier=supplier) # create shipment for order 1
    order.save()
    for line in order.lines.filter(type=OrderLineType.SHIPPING):
        total_charged += line.taxful_price.amount
    assert order.shipping_status == ShippingStatus.FULLY_SHIPPED
    supplier = get_simple_supplier()
    order_two, products = _get_order(False, True, True, identifier="1")
    order_two.shipping_address = shipping_address
    order_two.prices_include_tax = True
    order_two.save()
    assert order_two.shipping_status == ShippingStatus.NOT_SHIPPED
    order_two.create_shipment({x : Decimal("2") for x in products}, supplier=supplier) # create shipment for order 2

    for line in order_two.lines.filter(type=OrderLineType.SHIPPING):
        total_charged += line.taxless_price.amount
    order_two.create_payment(order_two.get_total_unpaid_amount()) # make sure shipment is paid
    order_two.save()
    assert order_two.is_paid()
    assert order_two.shipping_status == ShippingStatus.FULLY_SHIPPED
    assert not order.prices_include_tax # assert first order doesn't include taxes

    assert order_two.prices_include_tax # assert second order includes taxes
    assert order.shop == order_two.shop
    report = ShippingReport()
    report.shop = order.shop
    report.get_data()
    assert report.get_data()
    assert total_charged == report.get_data().get('data')[0].get('total_charged')
