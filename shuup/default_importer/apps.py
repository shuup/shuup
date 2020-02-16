# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.default_importer"
    provides = {
        "importers": [
            "shuup.default_importer.importers.ProductImporter",
            "shuup.default_importer.importers.PersonContactImporter",
            "shuup.default_importer.importers.CompanyContactImporter",
        ],
    }
