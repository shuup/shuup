# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.reports"
    provides = {
        "admin_module": ["shuup.reports.admin_module:ReportsAdminModule"],
        "report_writer_populator": ["shuup.reports.writer.populate_default_writers"]
    }
