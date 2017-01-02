# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.default_reports"
    provides = {
        "reports": [
            "shuup.default_reports.reports.sales:SalesReport",
            "shuup.default_reports.reports.total_sales:TotalSales",
            "shuup.default_reports.reports.sales_per_hour:SalesPerHour",
        ],
    }
