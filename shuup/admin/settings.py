# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
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
