# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import itertools
import json
import pytest
import pytz
import six
from babel.dates import format_date
from bs4 import BeautifulSoup
from datetime import date
from decimal import Decimal
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.safestring import SafeText
from django.utils.timezone import activate
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import override_provides
from shuup.core.models import Order
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.reports.admin_module.views import ReportView
from shuup.reports.forms import DateRangeChoices
from shuup.reports.report import ShuupReportBase
from shuup.reports.writer import (
    REPORT_WRITERS_MAP,
    CSVReportWriter,
    ExcelReportWriter,
    HTMLReportWriter,
    JSONReportWriter,
    PDFReportWriter,
    PprintReportWriter,
    ReportWriterPopulator,
    get_writer_instance,
)
from shuup.testing.factories import (
    create_order_with_product,
    get_default_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.i18n import get_current_babel_locale


def initialize_report_test(product_price, product_count, tax_rate, line_count):
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    expected_taxless_total = product_count * product_price
    expected_taxful_total = product_count * product_price * (1 + tax_rate)
    order = create_order_with_product(
        product=product,
        supplier=supplier,
        quantity=product_count,
        taxless_base_unit_price=product_price,
        tax_rate=tax_rate,
        n_lines=line_count,
        shop=shop,
    )
    order.create_payment(order.taxful_total_price.amount)
    order2 = create_order_with_product(
        product=product,
        supplier=supplier,
        quantity=product_count,
        taxless_base_unit_price=product_price,
        tax_rate=tax_rate,
        n_lines=line_count,
        shop=shop,
    )
    order2.create_payment(order2.taxful_total_price.amount)
    order2.set_canceled()  # Shouldn't affect reports
    return expected_taxful_total, expected_taxless_total, shop, order


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
        return (
            Order.objects.filter(shop=self.shop, order_date__range=(self.start_date, self.end_date))
            .valid()
            .paid()
            .order_by("order_date")
        )

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

            data.append(
                {
                    "date": format_date(order_date, format="short", locale=get_current_babel_locale()),
                    "order_count": order_count,
                    "product_count": int(product_count),
                    "taxless_total": taxless_total,
                    "taxful_total": taxful_total,
                }
            )

        return self.get_return_data(data)


class SalesTestReportForRequestTets(SalesTestReport):
    def get_objects(self):
        assert self.request
        return super(SalesTestReportForRequestTets, self).get_objects()

    def get_data(self):
        assert self.request
        return super(SalesTestReportForRequestTets, self).get_data()


@pytest.mark.django_db
def test_reporting(rf, admin_user):

    product_price = 100
    product_count = 2
    tax_rate = Decimal("0.10")
    line_count = 1

    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(
        product_price, product_count, tax_rate, line_count
    )

    with override_provides("reports", [__name__ + ":SalesTestReportForRequestTets"]):
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
        response_text = str(six.u(soup.encode("ascii")))
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
    with override_provides("report_writer_populator", ["shuup.reports.writer.populate_default_writers"]):
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
        product=product, supplier=supplier, quantity=1, taxless_base_unit_price=10, tax_rate=0, n_lines=2, shop=shop
    )
    order.create_payment(order.taxful_total_price.amount)

    data = {
        "report": SalesTestReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "html",
        "force_download": 1,
    }
    report = SalesTestReport(**data)

    for writer_cls in [
        ExcelReportWriter,
        PDFReportWriter,
        PprintReportWriter,
        HTMLReportWriter,
        JSONReportWriter,
        CSVReportWriter,
    ]:
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
    data = [
        {
            "date": "",
            "order_count": None,
            "product_count": 10,
            "taxless_total": TaxlessPrice("10", "EUR"),
            "taxful_total": TaxfulPrice("5", "EUR"),
        },
        {
            "date": "",
            "order_count": 12,
            "product_count": None,
            "taxless_total": TaxlessPrice("20", "EUR"),
            "taxful_total": None,
        },
    ]
    report = SalesTestReport(**report_data)
    totals = report.get_totals(data)
    expected = {
        "date": None,
        "order_count": 12,
        "product_count": 10,
        "taxless_total": TaxlessPrice("30", "EUR"),
        "taxful_total": TaxfulPrice("5", "EUR"),
    }
    assert totals == expected


@pytest.mark.parametrize("start_date,end_date", [(None, None), ("1990-01-01", None), (None, "2100-01-01")])
@pytest.mark.django_db
def test_none_dates(start_date, end_date):
    _, _, shop, order = initialize_report_test(10, 2, 0, 1)

    for timezone in ["UTC", "America/Sao_Paulo", "Etc/GMT+12", "Pacific/Kiritimati"]:
        with override_settings(TIME_ZONE=timezone):
            # Timezone needs to be activated to current one because some old timezone can still be active
            activate(pytz.timezone(timezone))
            data = {
                "report": SalesTestReport.get_name(),
                "shop": shop.pk,
                "start_date": start_date,
                "end_date": end_date,
                "writer": "json",
                "force_download": 1,
            }
            report = SalesTestReport(**data)
            data = report.get_data()
            assert data["data"]
