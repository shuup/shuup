# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from shoop.admin.base import AdminModule, MenuEntry, SearchResult
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.urls import get_model_url, derive_model_url, get_edit_and_list_urls
from shoop.core.models import Category
import six


class CategoryModule(AdminModule):
    name = _("Products")
    category = name
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:category.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^categories",
            view_template="shoop.admin.modules.categories.views.Category%sView",
            name_template="category.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Categories"), icon="fa fa-sitemap",
                url="shoop_admin:category.list", category=self.category
            )
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            categories = Category.objects.filter(
                Q(translations__name__icontains=query) |
                Q(identifier__icontains=query)
            ).distinct().order_by("tree_id", "lft")
            for i, category in enumerate(categories[:10]):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(category),
                    url=get_model_url(category),
                    category=self.category,
                    relevance=relevance
                )

    def get_model_url(self, object, kind):
        return derive_model_url(Category, "shoop_admin:category", object, kind)
