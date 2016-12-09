# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import requests
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule
from shuup.admin.dashboard import DashboardContentBlock
from shuup.core import cache

SECONDS_IN_DAY = 86400


class ShuupSupportModule(AdminModule):
    name = _("Shuup Support")

    def _get_resource(self, request, resource_id):
        cache_key = "SHUUPCOM_API_%s_%s" % (request.LANGUAGE_CODE, resource_id)
        resource = cache.get(cache_key)
        if not resource:
            try:
                r = requests.get("https://www.shuup.com/api/%s/?lang=%s" % (resource_id, request.LANGUAGE_CODE))
                resource = r.json()
                cache.set(cache_key, resource, timeout=SECONDS_IN_DAY)
            except Exception:
                pass
        return resource or {}

    def _get_faq_block(self, request):
        faqs = self._get_resource(request, "faq")
        if faqs.get("faqs"):
            faq_block = DashboardContentBlock.by_rendering_template(
                "faq", request, "shuup/admin/support/_faq_dashboard_block.jinja", faqs)
            faq_block.size = "small"
            return [faq_block]
        return []

    def _get_article_block(self, request):
        articles = self._get_resource(request, "articles")
        if articles.get("articles"):
            article_block = DashboardContentBlock.by_rendering_template(
                "articles", request, "shuup/admin/support/_articles_dashboard_block.jinja", articles)
            article_block.size = "small"
            return [article_block]
        return []

    def _get_support_block(self, request):
        support_block = DashboardContentBlock.by_rendering_template(
            "support", request, "shuup/admin/support/_support_dashboard_block.jinja", {})
        support_block.size = "small"
        return [support_block]

    def get_dashboard_blocks(self, request):
        blocks = []
        blocks.extend(self._get_faq_block(request))
        blocks.extend(self._get_article_block(request))
        blocks.extend(self._get_support_block(request))
        return blocks
