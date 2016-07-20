# -*- coding: utf-8 -*-
# This file is part of Shuup.
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
from filer.models import File

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import PRODUCTS_MENU_CATEGORY
from shuup.admin.utils.permissions import (
    get_default_model_permissions, get_permissions_from_urls
)
from shuup.admin.utils.search import split_query
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls, get_model_url,
    manipulate_query_string
)
from shuup.core.models import (
    Product, ProductCrossSell, ProductPackageLink, ProductVariationResult
)


class ProductModule(AdminModule):
    name = _("Products")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:product.list")

    def get_urls(self):
        return [
            admin_url(
                "^products/(?P<pk>\d+)/delete/$", "shuup.admin.modules.products.views.ProductDeleteView",
                name="product.delete",
                permissions=["shuup.delete_product"]
            ),
            admin_url(
                "^products/(?P<pk>\d+)/media/$", "shuup.admin.modules.products.views.ProductMediaEditView",
                name="product.edit_media",
                permissions=get_default_model_permissions(Product),
            ),
            admin_url(
                "^products/(?P<pk>\d+)/crosssell/$", "shuup.admin.modules.products.views.ProductCrossSellEditView",
                name="product.edit_cross_sell",
                permissions=get_default_model_permissions(ProductCrossSell),
            ),
            admin_url(
                "^products/(?P<pk>\d+)/variation/$", "shuup.admin.modules.products.views.ProductVariationView",
                name="product.edit_variation",
                permissions=get_default_model_permissions(ProductVariationResult),
            ),
            admin_url(
                "^products/(?P<pk>\d+)/package/$", "shuup.admin.modules.products.views.ProductPackageView",
                name="product.edit_package",
                permissions=get_default_model_permissions(ProductPackageLink),
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^products",
            view_template="shuup.admin.modules.products.views.Product%sView",
            name_template="product.%s",
            permissions=get_default_model_permissions(Product),
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Products"),
                icon="fa fa-cube",
                url="shuup_admin:product.list",
                category=PRODUCTS_MENU_CATEGORY,
                ordering=1
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
            url = reverse("shuup_admin:product.new")
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

    def get_required_permissions(self):
        return (
            get_permissions_from_urls(self.get_urls()) |
            get_default_model_permissions(Product) |
            get_default_model_permissions(File)
        )

    def get_model_url(self, object, kind):
        return derive_model_url(Product, "shuup_admin:product", object, kind)
