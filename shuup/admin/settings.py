# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

"""
Settings of Shuup Admin.

See :ref:`apps-settings` (in :obj:`shuup.apps`) for general information
about the Shuup settings system.  Especially, when inventing settings of
your own, the :ref:`apps-naming-settings` section is an important read.
"""

#: Spec which defines a list of Wizard Panes to be shown in Shuup Admin
#: for Shuup initialization and configuration.
#:
#: Panes must be subclasses of `shuup.admin.views.WizardPane`.
#:
SHUUP_SETUP_WIZARD_PANE_SPEC = []

#: Spec which defines a function that loads and return discovered admin modules.
#: This function should return a list of `shuup.admin.base.AdminModule`
#:
SHUUP_GET_ADMIN_MODULES_SPEC = ("shuup.admin.module_registry.get_admin_modules")

#: Spec which defines the Shop provider.
#: The shop provider is the interface responsible for fetching and setting
#: the active shop in admin module
#:
SHUUP_ADMIN_SHOP_PROVIDER_SPEC = ("shuup.admin.shop_provider.AdminShopProvider")
#: URL address to Shuup Merchant Documentation and Guide.
#: The URL must end with a slash.
#:
SHUUP_ADMIN_MERCHANT_DOCS_PAGE = "https://shuup-guide.readthedocs.io/en/latest/"

#: The minimum number of characters required to start a search
#:
SHUUP_ADMIN_MINIMUM_INPUT_LENGTH_SEARCH = 3

#: Spec that defines the Supplier Provider for a given request
#:
SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC = (
    "shuup.admin.supplier_provider.DefaultSupplierProvider")

#: The input format to be used in date pickers
#:
SHUUP_ADMIN_DATE_INPUT_FORMAT = "Y-m-d"

#: The input format to be used in datetime pickers
#:
SHUUP_ADMIN_DATETIME_INPUT_FORMAT = "Y-m-d H:i"

#: The input format to be used in time pickers
#:
SHUUP_ADMIN_TIME_INPUT_FORMAT = "H:i"
