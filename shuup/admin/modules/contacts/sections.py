# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from shuup.admin.base import Section
from shuup.core.models import PersonContact


class BasicInfoContactSection(Section):
    identifier = "contact_basic_info"
    name = _("Basic Information")
    icon = "fa-info-circle"
    template = "shuup/admin/contacts/_contact_basic_info.jinja"
    order = 1

    @classmethod
    def visible_for_object(cls, contact, request=None):
        return True

    @classmethod
    def get_context_data(cls, contact, request=None):
        context = {}

        context['groups'] = sorted(
            contact.groups.all_except_defaults(),
            key=(lambda x: force_text(x))
        )

        context['shops'] = sorted(
            contact.shops.all(),
            key=(lambda x: force_text(x))
        )

        context["companies"] = []
        if isinstance(contact, PersonContact):
            context["companies"] = sorted(
                contact.company_memberships.all(),
                key=(lambda x: force_text(x))
            )

        return context


class AddressesContactSection(Section):
    identifier = "contact_addresses"
    name = _("Addresses")
    icon = "fa-map-marker"
    template = "shuup/admin/contacts/_contact_addresses.jinja"
    order = 2

    @classmethod
    def visible_for_object(cls, contact, request=None):
        return (contact.default_shipping_address_id or
                contact.default_billing_address_id)

    @classmethod
    def get_context_data(cls, contact, request=None):
        return None


class OrdersContactSection(Section):
    identifier = "contact_orders"
    name = _("Orders")
    icon = "fa-inbox"
    template = "shuup/admin/contacts/_contact_orders.jinja"
    order = 3

    @classmethod
    def visible_for_object(cls, contact, request=None):
        return bool(contact.default_shipping_address_id or contact.default_billing_address_id)

    @classmethod
    def get_context_data(cls, contact, request=None):
        return contact.customer_orders.valid().order_by("-id")


class MembersContactSection(Section):
    identifier = "contact_members"
    name = _("Members")
    icon = "fa-user"
    template = "shuup/admin/contacts/_contact_members.jinja"
    order = 4

    @classmethod
    def visible_for_object(cls, contact, request=None):
        return hasattr(contact, 'members')

    @classmethod
    def get_context_data(cls, contact, request=None):
        if contact.members:
            return contact.members.all()

        return None
