# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.permissions import get_default_model_permissions
from shoop.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls
)
from shoop.core.models import ServiceProvider


class ServiceProviderModule(AdminModule):
    name = _("Service Providers")
    category = _("Payment and Shipping")

    def get_urls(self):
        return [
            admin_url(
                "^service_provider/(?P<pk>\d+)/delete/$",
                "shoop.admin.modules.service_providers.views.ServiceProviderDeleteView",
                name="service_provider.delete",
                permissions=["shoop.delete_serviceprovider"]
            )
        ] + get_edit_and_list_urls(
            url_prefix="^service_provider",
            view_template="shoop.admin.modules.service_providers.views.ServiceProvider%sView",
            name_template="service_provider.%s",
            permissions=get_default_model_permissions(ServiceProvider)
        )

    def get_menu_category_icons(self):
        return {self.category: "fa fa-cubes"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-truck",
                url="shoop_admin:service_provider.list",
                category=self.category
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(ServiceProvider)

    def get_model_url(self, object, kind):
        return derive_model_url(ServiceProvider, "shoop_admin:service_provider", object, kind)
