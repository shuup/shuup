# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import requests
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from requests.exceptions import RequestException

from shoop.admin.base import AdminModule, SearchResult
from shoop.admin.utils.urls import manipulate_query_string


class GuideAdminModule(AdminModule):
    def get_search_results(self, request, query):
        if settings.SHOOP_GUIDE_FETCH_RESULTS:
            try:
                response = requests.get(
                    settings.SHOOP_GUIDE_API_URL, timeout=settings.SHOOP_GUIDE_TIMEOUT_LIMIT, params={"q": query}
                )
                json = response.json()
                results = json["results"]["hits"]["hits"]
                for result in results:
                    title = result["fields"]["title"][0]
                    link = result["fields"]["link"] + ".html"
                    url = manipulate_query_string(link, highlight=query)
                    yield SearchResult(
                        text=_("Guide: %s") % title,
                        url=url,
                        is_action=True,
                        relevance=0,
                        target="_blank",
                    )
            except RequestException:
                # Catch timeout or network errors so as not to break the search
                pass
        else:
            url = manipulate_query_string(settings.SHOOP_GUIDE_LINK_URL, q=query)
            yield SearchResult(
                text=_("Search guide for: \"%s\"") % query,
                url=url,
                is_action=True,
                relevance=0,
                target="_blank"
            )
