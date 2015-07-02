# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.db.models import Count
from django.utils.translation import ugettext as _
from shoop.admin.utils.picotable import Column, true_or_false_filter, RangeFilter, TextFilter
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Contact, PersonContact, CompanyContact


class ContactListView(PicotableListView):
    model = Contact
    columns = [
        Column("name", _(u"Name"), linked=True, filter_config=TextFilter()),
        Column("type", _(u"Type"), display="get_type_display", sortable=False),  # TODO: Add a filter
        Column("email", _(u"Email"), filter_config=TextFilter()),
        Column("phone", _(u"Phone"), filter_config=TextFilter()),
        Column("is_active", _(u"Active"), filter_config=true_or_false_filter),
        Column("n_orders", _(u"# Orders"), class_name="text-right", filter_config=RangeFilter(step=1)),
    ]

    def get_queryset(self):
        return super(ContactListView, self).get_queryset().annotate(n_orders=Count("customer_orders"))

    def get_type_display(self, instance):
        if isinstance(instance, PersonContact):
            return _(u"Person")
        elif isinstance(instance, CompanyContact):
            return _(u"Company")
        else:
            return _(u"Contact")

    def get_object_abstract(self, instance, item):
        """
        :type instance: shoop.core.models.contacts.Contact
        """
        bits = filter(None, [
            item["type"],
            _("Active") if instance.is_active else _("Inactive"),
            _("Email: %s") % (instance.email or "\u2014"),
            _("Phone: %s") % (instance.phone or "\u2014"),
            _("%d orders") % instance.n_orders,
        ])
        return [
            {"text": instance.name or _("Contact"), "class": "header"},
            {"text": ", ".join(bits)}
        ]
