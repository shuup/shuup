# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.configuration import get as original_configuration_get
from shuup.core.setting_keys import (
    SHUUP_ENABLE_MULTIPLE_SHOPS,
    SHUUP_ENABLE_MULTIPLE_SUPPLIERS,
    SHUUP_MANAGE_CONTACTS_PER_SHOP,
)
from shuup_tests.utils import replace_urls


def get_admin_only_urls():
    from django.conf.urls import include, url

    from shuup.admin.urls import get_urls

    class FauxUrlPatternsModule:
        app_name = "shuup_admin"
        urlpatterns = get_urls()

    return [
        url(r"^sa/", include(FauxUrlPatternsModule, namespace="shuup_admin")),
    ]


def admin_only_urls():
    return replace_urls(get_admin_only_urls())


def get_multiple_shops_true_multiple_suppliers_false_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SHOPS:
        return True
    if key == SHUUP_ENABLE_MULTIPLE_SUPPLIERS:
        return False
    return original_configuration_get(shop, key, default)


def get_multiple_shops_true_multiple_suppliers_true_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SHOPS:
        return True
    if key == SHUUP_ENABLE_MULTIPLE_SUPPLIERS:
        return True
    return original_configuration_get(shop, key, default)


def get_multiple_shops_false_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SHOPS:
        return False
    return original_configuration_get(shop, key, default)


def get_multiple_shops_true_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SHOPS:
        return True
    return original_configuration_get(shop, key, default)


def get_multiple_shops_true_contacts_per_shop_true_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SHOPS:
        return True
    if key == SHUUP_MANAGE_CONTACTS_PER_SHOP:
        return True
    return original_configuration_get(shop, key, default)


def get_multiple_suppliers_true_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SUPPLIERS:
        return True
    return original_configuration_get(shop, key, default)


def get_multiple_suppliers_false_configuration(shop, key, default=None):
    if key == SHUUP_ENABLE_MULTIPLE_SUPPLIERS:
        return False
    return original_configuration_get(shop, key, default)
