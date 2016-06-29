# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.utils.permissions import (
    get_default_model_permissions, get_permissions_from_urls
)
from shuup.admin.utils.urls import admin_url, derive_model_url, get_model_url
from shuup.core.models import Contact

from .dashboard import get_active_customers_block


class ContactModule(AdminModule):
    name = _("Contacts")
    category = name
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:contact.list")

    def get_urls(self):
        return [
            admin_url(
                "^contacts/new/$",
                "shuup.admin.modules.contacts.views.ContactEditView",
                kwargs={"pk": None},
                name="contact.new",
                permissions=["shuup.add_contact"],
            ),
            admin_url(
                "^contacts/(?P<pk>\d+)/edit/$",
                "shuup.admin.modules.contacts.views.ContactEditView",
                name="contact.edit",
                permissions=["shuup.change_contact"],
            ),
            admin_url(
                "^contacts/(?P<pk>\d+)/$",
                "shuup.admin.modules.contacts.views.ContactDetailView",
                name="contact.detail",
                permissions=get_default_model_permissions(Contact),
            ),
            admin_url(
                "^contacts/reset-password/(?P<pk>\d+)/$",
                "shuup.admin.modules.contacts.views.ContactResetPasswordView",
                name="contact.reset_password",
                permissions=get_default_model_permissions(Contact),
            ),
            admin_url(
                "^contacts/$",
                "shuup.admin.modules.contacts.views.ContactListView",
                name="contact.list",
                permissions=get_default_model_permissions(Contact),
            ),
        ]

    def get_menu_category_icons(self):
        return {self.category: "fa fa-users"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Contacts"), icon="fa fa-users",
                url="shuup_admin:contact.list", category=self.category
            )
        ]

    def get_required_permissions(self):
        return get_permissions_from_urls(self.get_urls()) | get_default_model_permissions(Contact)

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
        return derive_model_url(Contact, "shuup_admin:contact", object, kind)
