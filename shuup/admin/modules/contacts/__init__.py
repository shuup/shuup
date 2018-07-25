# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import CONTACTS_MENU_CATEGORY
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import admin_url, derive_model_url, get_model_url
from shuup.core.models import CompanyContact, Contact, PersonContact


class ContactModule(AdminModule):
    name = _("Contacts")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:contact.list", category=CONTACTS_MENU_CATEGORY)

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
            admin_url(
                "^contacts/list-settings/",
                "shuup.admin.modules.settings.views.ListSettingsView",
                name="contact.list_settings",
                permissions=get_default_model_permissions(Contact),
            ),
            admin_url(
                "^contacts/mass-edit/$", "shuup.admin.modules.contacts.views.ContactMassEditView",
                name="contact.mass_edit",
                permissions=get_default_model_permissions(Contact)
            ),
            admin_url(
                "^contacts/mass-edit-group/$", "shuup.admin.modules.contacts.views.ContactGroupMassEditView",
                name="contact.mass_edit_group",
                permissions=get_default_model_permissions(Contact)
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Contacts"), icon="fa fa-users",
                url="shuup_admin:contact.list", category=CONTACTS_MENU_CATEGORY,
                ordering=1
            )
        ]

    def get_required_permissions(self):
        return (
            get_default_model_permissions(CompanyContact) |
            get_default_model_permissions(Contact) |
            get_default_model_permissions(PersonContact)
        )

    def get_search_results(self, request, query):
        if len(query) >= self.minimum_search_length:
            filters = Q(Q(name__icontains=query) | Q(email=query))

            # show only contacts which the shop has access
            if settings.SHUUP_ENABLE_MULTIPLE_SHOPS and settings.SHUUP_MANAGE_CONTACTS_PER_SHOP:
                shop = get_shop(request)
                filters &= Q(groups__shop=shop)

            contacts = Contact.objects.filter(filters)
            for i, contact in enumerate(contacts[:10]):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(contact), url=get_model_url(contact),
                    category=_("Contacts"), relevance=relevance
                )

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Contact, "shuup_admin:contact", object, kind)
