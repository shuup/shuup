# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.utils.encoding import force_text

from shuup.admin.module_registry import replace_modules
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.apps.provides import override_provides
from shuup.default_reports.reports.sales import SalesReport
from shuup.default_reports.reports.sales_per_hour import SalesPerHour
from shuup.default_reports.reports.total_sales import TotalSales
from shuup.reports.admin_module import ReportsAdminModule
from shuup.reports.admin_module.views import ReportView
from shuup.testing.factories import (
    get_default_permission_group,
    get_default_shop,
    get_default_staff_user,
    get_default_tax_class,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.admin.utils import admin_only_urls

REPORTS = [
    "shuup.default_reports.reports.sales:SalesReport",
    "shuup.default_reports.reports.total_sales:TotalSales",
    "shuup.default_reports.reports.sales_per_hour:SalesPerHour",
]


@pytest.mark.django_db
def test_reports_admin_permissions(rf):
    shop = get_default_shop()  # We need a shop to exists
    staff_user = get_default_staff_user(shop)
    permission_group = get_default_permission_group()
    staff_user.groups.add(permission_group)
    request = apply_request_middleware(rf.get("/"), user=staff_user)
    request.user = staff_user

    with replace_modules([ReportsAdminModule]):
        with override_provides("reports", REPORTS):
            extra_permissions = ReportsAdminModule().get_extra_permissions()
            assert len(extra_permissions) == 3
            assert SalesReport.identifier in extra_permissions
            assert TotalSales.identifier in extra_permissions
            assert SalesPerHour.identifier in extra_permissions
            with admin_only_urls():
                view_func = ReportView.as_view()
                response = view_func(request)
                response.render()
                response = view_func(request, pk=None)  # "new mode"
                response.render()
                assert response.content
                soup = BeautifulSoup(response.content)
                assert soup.find("div", {"class": "content-block"}).text == "No reports available"
                expected_report_identifiers = []
                for report_cls in [SalesReport, TotalSales, SalesPerHour]:
                    expected_report_identifiers.append(report_cls.identifier)
                    set_permissions_for_group(permission_group, [report_cls.identifier])

                    response = view_func(request, pk=None)  # "new mode"
                    response.render()
                    assert response.content
                    soup = BeautifulSoup(response.content)
                    for option in soup.find("select", {"id": "id_report"}).findAll("option"):
                        assert option["value"] in expected_report_identifiers
