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
from shoop.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shoop.core.models import ContactGroup


class ContactGroupModule(AdminModule):
    name = _("Contact Groups")
    category = _("Contacts")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:contact-group.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^contact-groups",
            view_template="shoop.admin.modules.contact_groups.views.ContactGroup%sView",
            name_template="contact-group.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-asterisk",
                url="shoop_admin:contact-group.list",
                category=self.category
            ),
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(ContactGroup, "shoop_admin:contact-group", object, kind)
