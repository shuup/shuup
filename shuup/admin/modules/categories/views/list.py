# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Category, CategoryStatus, CategoryVisibility


class CategoryListView(PicotableListView):
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

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Status"), "text": item["status"]},
            {"title": _(u"Parent"), "text": item["parent"]} if instance.parent_id else None
        ]
