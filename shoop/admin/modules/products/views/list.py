# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from shoop.admin.utils.picotable import Column, TextFilter
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Product
from django.utils.translation import ugettext_lazy as _


class ProductListView(PicotableListView):
    model = Product
    columns = [
        Column("sku", _(u"SKU"), display="sku", filter_config=TextFilter(placeholder=_("Filter by SKU..."))),
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("type", _(u"Type")),
        Column("category", _(u"Primary Category")),
    ]

    def get_queryset(self):
        return Product.objects.all_except_deleted()

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"SKU"), "text": item["sku"]},
            {"title": _(u"Type"), "text": item["type"]},
            {"title": _(u"Primary Category"), "text": item["category"]}
        ]
