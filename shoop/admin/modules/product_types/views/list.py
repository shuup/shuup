# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.db.models import Count
from django.views.generic import ListView
from shoop.admin.toolbar import Toolbar, NewActionButton
from shoop.admin.utils.picotable import Column, PicotableViewMixin, TextFilter
from shoop.core.models import ProductType
from django.utils.translation import ugettext_lazy as _


class ProductTypeListView(PicotableViewMixin, ListView):
    model = ProductType
    columns = [
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("n_attributes", _(u"Number of Attributes")),
    ]

    def get_queryset(self):
        return ProductType.objects.all().annotate(n_attributes=Count("attributes"))

    def get_context_data(self, **kwargs):
        context = super(ProductTypeListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([NewActionButton("shoop_admin:product-type.new")])
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
        ]
