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
from shuup.admin.menu import CONTACTS_MENU_CATEGORY
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.core.models import ContactGroupPriceDisplay


class ContactGroupPriceDisplayModule(AdminModule):
    name = _("Contact Group Pricing Display")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:contact_group_price_display.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^contact_group_price_display",
            view_template="shuup.admin.modules.contact_group_price_display.views.ContactGroupPriceDisplay%sView",
            name_template="contact_group_price_display.%s",
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-asterisk",
                url="shuup_admin:contact_group_price_display.list",
                category=CONTACTS_MENU_CATEGORY,
                ordering=3,
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(ContactGroupPriceDisplay, "shuup_admin:contact_group_price_display", object, kind)
