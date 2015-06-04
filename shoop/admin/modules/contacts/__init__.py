# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from shoop.admin.base import AdminModule, MenuEntry, SearchResult
from django.utils.translation import ugettext_lazy as _
from .dashboard import get_active_customers_block
from shoop.admin.utils.urls import admin_url, get_model_url, derive_model_url
from shoop.core.models import Contact
import six


class ContactModule(AdminModule):
    name = _("Contacts")
    category = name
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:contact.list")

    def get_urls(self):
        return [
            admin_url(
                "^contacts/new/$",
                "shoop.admin.modules.contacts.views.ContactEditView",
                kwargs={"pk": None},
                name="contact.new"
            ),
            admin_url(
                "^contacts/(?P<pk>\d+)/edit/$",
                "shoop.admin.modules.contacts.views.ContactEditView",
                name="contact.edit"
            ),
            admin_url(
                "^contacts/(?P<pk>\d+)/$",
                "shoop.admin.modules.contacts.views.ContactDetailView",
                name="contact.detail"
            ),
            admin_url(
                "^contacts/reset-password/(?P<pk>\d+)/$",
                "shoop.admin.modules.contacts.views.ContactResetPasswordView",
                name="contact.reset_password"
            ),
            admin_url(
                "^contacts/$",
                "shoop.admin.modules.contacts.views.ContactListView",
                name="contact.list"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.category: "fa fa-users"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Contacts"), icon="fa fa-users",
                url="shoop_admin:contact.list", category=self.category
            )
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            contacts = Contact.objects.filter(
                Q(name__icontains=query) |
                Q(email=query)
            )
            for i, contact in enumerate(contacts[:10]):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(contact), url=get_model_url(contact),
                    category=self.category, relevance=relevance
                )

    def get_dashboard_blocks(self, request):
        yield get_active_customers_block(request)

    def get_model_url(self, object, kind):
        return derive_model_url(Contact, "shoop_admin:contact", object, kind)
