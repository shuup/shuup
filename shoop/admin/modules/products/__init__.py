# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import Counter

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry, SearchResult
from shoop.admin.utils.search import split_query
from shoop.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls, get_model_url,
    manipulate_query_string
)
from shoop.core.models import Product


class ProductModule(AdminModule):
    name = _("Products")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:product.list")

    def get_urls(self):
        return [
            admin_url(
                "^products/(?P<pk>\d+)/delete/$", "shoop.admin.modules.products.views.ProductDeleteView",
                name="product.delete"
            ),
            admin_url(
                "^products/(?P<pk>\d+)/media/$", "shoop.admin.modules.products.views.ProductMediaEditView",
                name="product.edit_media"
            ),
            admin_url(
                "^products/(?P<pk>\d+)/crosssell/$", "shoop.admin.modules.products.views.ProductCrossSellEditView",
                name="product.edit_cross_sell"
            ),
            admin_url(
                "^products/(?P<pk>\d+)/variation/$", "shoop.admin.modules.products.views.ProductVariationView",
                name="product.edit_variation"
            ),
            admin_url(
                "^products/(?P<pk>\d+)/package/$", "shoop.admin.modules.products.views.ProductPackageView",
                name="product.edit_package"
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^products",
            view_template="shoop.admin.modules.products.views.Product%sView",
            name_template="product.%s"
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-cube"}

    def get_menu_entries(self, request):
        category = _("Products")
        return [
            MenuEntry(
                text=_("Products"),
                icon="fa fa-cube",
                url="shoop_admin:product.list",
                category=category
            )
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        skus_seen = set()
        if len(query) >= minimum_query_length:
            pk_counter = Counter()
            pk_counter.update(Product.objects.filter(sku__startswith=query).values_list("pk", flat=True))
            name_q = Q()
            for part in split_query(query, minimum_query_length):
                name_q &= Q(name__icontains=part)
            pk_counter.update(
                Product._parler_meta.root_model.objects.filter(name_q).values_list("master_id", flat=True)
            )
            pks = [pk for (pk, count) in pk_counter.most_common(10)]
            for product in Product.objects.filter(pk__in=pks):
                relevance = 100 - pk_counter.get(product.pk, 0)
                skus_seen.add(product.sku.lower())
                yield SearchResult(
                    text=force_text(product),
                    url=get_model_url(product),
                    category=_("Products"),
                    relevance=relevance
                )

        if len(query) >= minimum_query_length:
            url = reverse("shoop_admin:product.new")
            if " " in query:
                yield SearchResult(
                    text=_("Create Product Called \"%s\"") % query,
                    url=manipulate_query_string(url, name=query),
                    is_action=True
                )
            else:
                if query.lower() not in skus_seen:
                    yield SearchResult(
                        text=_("Create Product with SKU \"%s\"") % query,
                        url=manipulate_query_string(url, sku=query),
                        is_action=True
                    )

    def get_model_url(self, object, kind):
        return derive_model_url(Product, "shoop_admin:product", object, kind)
