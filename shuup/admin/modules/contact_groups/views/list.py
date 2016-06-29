# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from shuup.admin.toolbar import NewActionButton, Toolbar
from shuup.admin.utils.picotable import Column, PicotableViewMixin, TextFilter
from shuup.core.models import ContactGroup


class ContactGroupListView(PicotableViewMixin, ListView):
    model = ContactGroup
    columns = [
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("n_members", _(u"Number of Members")),
    ]

    def get_queryset(self):
        return ContactGroup.objects.all().annotate(n_members=Count("members"))

    def get_context_data(self, **kwargs):
        context = super(ContactGroupListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([NewActionButton("shuup_admin:contact-group.new")])
        return context
