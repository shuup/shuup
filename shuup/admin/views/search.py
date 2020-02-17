# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from itertools import chain

from django.http.response import JsonResponse
from django.views.generic import View

from shuup.admin.base import SearchResult
from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.utils.search import FuzzyMatcher


def get_search_results(request, query):
    fuzzer = FuzzyMatcher(query)
    normal_results = []
    menu_entry_results = []
    for module in get_modules():
        if get_missing_permissions(request.user, module.get_required_permissions()):
            continue

        normal_results.extend(module.get_search_results(request, query) or ())
        for menu_entry in module.get_menu_entries(request) or ():
            texts = (menu_entry.get_search_query_texts() or ())
            if any(fuzzer.test(text) for text in texts):
                menu_entry_results.append(SearchResult(
                    text=menu_entry.text,
                    url=menu_entry.url,
                    icon=menu_entry.icon,
                    category=menu_entry.category,
                    relevance=90,
                    is_action=True
                ))
    results = sorted(
        chain(normal_results, menu_entry_results),
        key=lambda r: r.relevance,
        reverse=True
    )
    return results


class SearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("q")
        if query:
            results = get_search_results(request, query)
        else:
            results = []
        return JsonResponse({"results": [r.to_json() for r in results]})
