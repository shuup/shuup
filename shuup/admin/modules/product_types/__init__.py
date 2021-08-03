# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from typing import Iterable

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import STOREFRONT_MENU_CATEGORY
from shuup.admin.utils.object_selector import get_object_selector_permission_name
from shuup.admin.utils.urls import admin_url, derive_model_url, get_edit_and_list_urls
from shuup.core.models import ProductType


class ProductTypeModule(AdminModule):
    name = _("Product Types")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:product_type.list")

    def get_urls(self):
        return [
            admin_url(
                r"^product-types/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.product_types.views.ProductTypeDeleteView",
                name="product_type.delete",
            )
        ] + get_edit_and_list_urls(
            url_prefix="^product-types",
            view_template="shuup.admin.modules.product_types.views.ProductType%sView",
            name_template="product_type.%s",
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Product types"),
                icon="fa fa-asterisk",
                url="shuup_admin:product_type.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=3,
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(ProductType, "shuup_admin:product_type", object, kind)

    def get_extra_permissions(self) -> Iterable[str]:
        return [get_object_selector_permission_name(ProductType)]

    def get_permissions_help_texts(self) -> Iterable[str]:
        return {get_object_selector_permission_name(ProductType): _("Allow the user to select product types in admin.")}
