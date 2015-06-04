# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.views.generic import ListView
from shoop.admin.toolbar import Toolbar, NewActionButton
from shoop.admin.utils.picotable import Column, PicotableViewMixin, ChoicesFilter, TextFilter
from shoop.core.models import Category, CategoryStatus, CategoryVisibility
from django.utils.translation import ugettext_lazy as _


class CategoryListView(PicotableViewMixin, ListView):
    model = Category
    columns = [
        Column(
            "name", _(u"Name"), sort_field="translations__name", display="name", linked=True,
            filter_config=TextFilter(
                filter_field="translations__name",
                placeholder=_("Filter by name...")
            )
        ),
        Column("status", _(u"Status"), filter_config=ChoicesFilter(choices=CategoryStatus.choices)),
        Column("visibility", _(u"Visibility"), filter_config=ChoicesFilter(choices=CategoryVisibility.choices)),
        Column("parent", _(u"Parent"), sortable=False, display="parent"),
    ]

    def get_queryset(self):
        return Category.objects.all_except_deleted()

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([NewActionButton("shoop_admin:category.new")])
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Status"), "text": item["status"]},
            {"title": _(u"Parent"), "text": item["parent"]} if instance.parent_id else None
        ]
