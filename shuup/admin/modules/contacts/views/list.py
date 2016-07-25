# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models import Count, Q
from django.utils.translation import ugettext as _

from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, RangeFilter, TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import (
    CompanyContact, Contact, ContactGroup, PersonContact
)


class ContactListView(PicotableListView):
    model = Contact
    columns = [
        Column("name", _(u"Name"), linked=True, filter_config=TextFilter()),
        Column("type", _(u"Type"), display="get_type_display", sortable=False),  # TODO: Add a filter
        Column("email", _(u"Email"), filter_config=TextFilter()),
        Column("phone", _(u"Phone"), filter_config=TextFilter()),
        Column(
            "is_active",
            _(u"Active"),
            filter_config=ChoicesFilter([(False, _("no")), (True, _("yes"))], default=True)
        ),
        Column("n_orders", _(u"# Orders"), class_name="text-right", filter_config=RangeFilter(step=1)),
        Column("groups", _("Groups"), filter_config=ChoicesFilter(ContactGroup.objects.all(), "groups"))
    ]

    def get_queryset(self):
        groups = self.get_filter().get("groups")
        query = Q(groups__in=groups) if groups else Q()
        return (
            super(ContactListView, self).get_queryset()
            .filter(query)
            .annotate(n_orders=Count("customer_orders"))
            .order_by("-created_on"))

    def get_type_display(self, instance):
        if isinstance(instance, PersonContact):
            return _(u"Person")
        elif isinstance(instance, CompanyContact):
            return _(u"Company")
        else:
            return _(u"Contact")

    def get_object_abstract(self, instance, item):
        """
        :type instance: shuup.core.models.Contact
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
