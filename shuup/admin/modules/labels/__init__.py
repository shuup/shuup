# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import STOREFRONT_MENU_CATEGORY
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.core.models import Label


class LabelsModule(AdminModule):
    name = _("Labels")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:label.list")

    def get_urls(self):
        from shuup.admin.urls import admin_url

        delete = admin_url(
            r"^labels/(?P<pk>\d+)/delete/$", "shuup.admin.modules.labels.views.LabelDeleteView", name="label.delete"
        )

        return [delete] + get_edit_and_list_urls(
            url_prefix="^labels", view_template="shuup.admin.modules.labels.views.Label%sView", name_template="label.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-sitemap",
                url="shuup_admin:label.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=5,
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Label, "shuup_admin:label", object, kind)
