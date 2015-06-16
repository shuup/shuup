# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from shoop.admin.base import AdminModule, MenuEntry
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.urls import admin_url, derive_model_url
from shoop.core.models import ContactGroup


class ContactGroupModule(AdminModule):
    name = _("Contact Groups")
    category = _("Contacts")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:contact-group.list")

    def get_urls(self):
        return [
            admin_url(
                "^contact-groups/(?P<pk>\d+)/$",
                "shoop.admin.modules.contact_groups.views.ContactGroupEditView",
                name="contact-group.edit"),
            admin_url(
                "^contact-groups/new/$",
                "shoop.admin.modules.contact_groups.views.ContactGroupEditView",
                kwargs={"pk": None},
                name="contact-group.new"
            ),
            admin_url(
                "^contact-groups/$",
                "shoop.admin.modules.contact_groups.views.ContactGroupListView",
                name="contact-group.list"
            ),
        ]

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
