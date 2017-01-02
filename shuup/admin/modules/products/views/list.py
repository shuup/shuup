# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, RangeFilter, TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import ProductMode, Shop, ShopProduct


class ProductListView(PicotableListView):
    model = ShopProduct

    default_columns = [
        Column("primary_image", _(u"Primary Image"),
               display="get_primary_image", class_name="text-center", raw=True, ordering=1, sortable=False),
        Column("name", _(u"Name"),
               sort_field="product__translations__name",
               display="product__name",
               filter_config=TextFilter(
                   filter_field="product__translations__name", placeholder=_("Filter by name...")
               ),
               ordering=2),
        Column("sku", _(u"SKU"),
               display="product__sku", filter_config=RangeFilter(filter_field="product__sku"), ordering=3),
        Column("barcode", _(u"Barcode"),
               display="product__barcode", filter_config=TextFilter(_("Filter by barcode...")), ordering=4),
        Column("type", _(u"Type"), display="product__type", ordering=5),
        Column("mode", _(u"Mode"),
               display="product__mode", filter_config=ChoicesFilter(ProductMode.choices), ordering=6),
    ]

    related_objects = [
        ("product", "shuup.core.models:Product"),
    ]

    mass_actions = [
        "shuup.admin.modules.products.mass_actions:VisibleMassAction",
        "shuup.admin.modules.products.mass_actions:InvisibleMassAction",
        "shuup.admin.modules.products.mass_actions:FileResponseAction",
        "shuup.admin.modules.products.mass_actions:EditProductAttributesAction",
    ]

    def get_primary_image(self, instance):
        if instance.product.primary_image:
            return "<img src='/media/%s'>" % instance.product.primary_image.get_thumbnail()
        else:
            return "<img src='%s'>" % static("shuup_admin/img/no_image_thumbnail.png")

    def get_queryset(self):
        filter = self.get_filter()
        shop_id = filter.get("shop", Shop.objects.first().pk)
        qs = ShopProduct.objects.filter(product__deleted=False, shop_id=shop_id)
        q = Q()
        for mode in filter.get("modes", []):
            q |= Q(product__mode=mode)
        manufacturer_ids = filter.get("manufacturers")
        if manufacturer_ids:
            q |= Q(product__manufacturer_id__in=manufacturer_ids)
        qs = qs.filter(q)
        return qs

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance.product, "class": "header"},
            {"title": _(u"Barcode"), "text": item.get("product__barcode")},
            {"title": _(u"SKU"), "text": item.get("product__sku")},
            {"title": _(u"Type"), "text": item.get("product__type")},
        ]
