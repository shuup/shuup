# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Category, Product, ProductMode


class ProductListView(PicotableListView):
    model = Product
    default_columns = [
        Column("sku", _(u"SKU"), display="sku", filter_config=TextFilter(placeholder=_("Filter by SKU..."))),
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("barcode", _(u"Barcode"), display="barcode", filter_config=TextFilter(_("Filter by barcode..."))),
        Column("type", _(u"Type")),
        Column("mode", _(u"Mode"), filter_config=ChoicesFilter(ProductMode.choices)),
        Column("category", _(u"Primary Category"), filter_config=ChoicesFilter(Category.objects.all(), "category")),
    ]

    def get_queryset(self):
        filter = self.get_filter()
        shop_id = filter.get("shop")
        qs = Product.objects.all_except_deleted()
        q = Q()
        for mode in filter.get("modes", []):
            q |= Q(mode=mode)
        manufacturer_ids = filter.get("manufacturers")
        if manufacturer_ids:
            q |= Q(manufacturer_id__in=manufacturer_ids)
        qs = qs.filter(q)
        if shop_id:
            qs = qs.filter(shop_products__shop_id=int(shop_id))
        return qs

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Barcode"), "text": item.get("barcode")},
            {"title": _(u"SKU"), "text": item.get("sku")},
            {"title": _(u"Type"), "text": item.get("type")},
            {"title": _(u"Primary Category"), "text": item.get("category")}
        ]
