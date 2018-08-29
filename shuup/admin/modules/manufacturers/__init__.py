# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import STOREFRONT_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.core.models import Manufacturer


class ManufacturerModule(AdminModule):
    name = _("Manufacturers")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:manufacturer.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^manufacturers",
            view_template="shuup.admin.modules.manufacturers.views.Manufacturer%sView",
            name_template="manufacturer.%s",
            permissions=get_default_model_permissions(Manufacturer),
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Manufacturers"),
                icon="fa fa-building",
                url="shuup_admin:manufacturer.list",
                category=STOREFRONT_MENU_CATEGORY,
                subcategory="settings",
                ordering=4
            ),
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(Manufacturer) | get_default_model_permissions(File)

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Manufacturer, "shuup_admin:manufacturer", object, kind)
