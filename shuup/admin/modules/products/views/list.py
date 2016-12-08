# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, RangeFilter, TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Product, ProductMode


class ProductListView(PicotableListView):
    model = Product
    default_columns = [
        Column("primary_image", _(u"Primary Image"), display="get_primary_image",
               class_name="text-center", raw=True, ordering=1, sortable=False),
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        ), ordering=2),
        Column("sku", _(u"SKU"), display="sku", filter_config=RangeFilter(), ordering=3),
        Column("barcode", _(u"Barcode"),
               display="barcode", filter_config=TextFilter(_("Filter by barcode...")), ordering=4),
        Column("type", _(u"Type"), ordering=5),
        Column("mode", _(u"Mode"), filter_config=ChoicesFilter(ProductMode.choices), ordering=6),
    ]

    mass_actions = [
        "shuup.admin.modules.products.mass_actions:VisibleMassAction",
        "shuup.admin.modules.products.mass_actions:InvisibleMassAction",
        "shuup.admin.modules.products.mass_actions:FileResponseAction",
        "shuup.admin.modules.products.mass_actions:EditProductAttributesAction",
    ]

    def get_primary_image(self, instance):
        if instance.primary_image:
            return "<img src='/media/%s'>" % instance.primary_image.get_thumbnail()
        else:
            return "<img src='%s'>" % static("shuup_admin/img/no_image_thumbnail.png")

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
        ]
