# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
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


#: The input step to be used for time pickers
#:
SHUUP_ADMIN_DATETIME_INPUT_STEP = 15

#: Menu category identifiers that should always activate the
#: menu item. Useful in case there is need to always open some
#: certain menus.
SHUUP_ALWAYS_ACTIVE_MENU_CATEGORY_IDENTIFIERS = []

#: Get front URL for admin panel navigation bar. Override
#: for example for custom domain logic when admin panel is used
#: from shared marketplace URL.
SHUUP_ADMIN_NAVIGATION_GET_FRONT_URL_SPEC = ("shuup.admin.utils.urls.get_front_url")

#: Indicates which objects select fields should load options asynchronously.
#: When enabled, fields will load options through AJAX requests instead
#: of generating them while rendering the page. For enviroments with huge amount of options
#: in fields, like categories, it is best to have this enabled.
#: When disabled, the options will be rendered on page load whenever it is possible, as
#: in some features, the asynchronous load is not an option.
#:
SHUUP_ADMIN_LOAD_SELECT_OBJECTS_ASYNC = {
    "categories": True,
    "suppliers": True
}

#: Indicates the authentication form class that should be used in login views inside Admin
#:
SHUUP_ADMIN_AUTH_FORM_SPEC = ("shuup.admin.forms.EmailAuthenticationForm")

#: To which view redirect impersonator when login as regular user
#:
SHUUP_ADMIN_LOGIN_AS_REDIRECT_VIEW = "shuup:index"

#: To which view redirect impersonator when login as staff
#:
SHUUP_ADMIN_LOGIN_AS_STAFF_REDIRECT_VIEW = "shuup_admin:dashboard"
