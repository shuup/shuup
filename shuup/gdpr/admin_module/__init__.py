# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import admin_url
from shuup.core.models import Contact
from shuup.gdpr.models import GDPRSettings


class GDPRModule(AdminModule):
    name = _("GDPR")

    def get_urls(self):
        return [
            admin_url(
                "^gdpr/$",
                "shuup.gdpr.admin_module.views.GDPRView",
                name="gdpr.settings",
                permissions=get_default_model_permissions(GDPRSettings)
            ),
            admin_url(
                "^gdpr/contact/(?P<pk>\d+)/anonymize/$",
                "shuup.gdpr.admin_module.views.GDPRAnonymizeView",
                name="gdpr.anonymize",
                permissions=get_default_model_permissions(Contact)
            ),
            admin_url(
                "^gdpr/contact/(?P<pk>\d+)/download/$",
                "shuup.gdpr.admin_module.views.GDPRDownloadDataView",
                name="gdpr.download_data",
                permissions=get_default_model_permissions(Contact)
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("GDPR"),
                icon="fa fa-shield",
                url="shuup_admin:gdpr.settings",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="other_settings",
            ),
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(GDPRSettings)
