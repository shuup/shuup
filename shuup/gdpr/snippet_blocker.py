# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
from django.conf import settings

from shuup.xtheme.models import Snippet
from shuup.xtheme.resources import SnippetBlocker


class GDPRSnippetBlocker(SnippetBlocker):
    @classmethod
    def should_block_global_snippet_injection(cls, snippet: Snippet, context: dict):
        gdpr_cookies = list(snippet.blocked_gdpr_cookies.values_list("cookies", flat=True))

        request = context.get("request")
        if not request or not request.COOKIES.get(settings.SHUUP_GDPR_CONSENT_COOKIE_NAME):
            # block if there is some configured cookie that needs to be consented
            # and there is no way of detecting it
            return bool(gdpr_cookies)

        unique_cookies = set()
        for gdpr_cookie in gdpr_cookies:
            for cookie in gdpr_cookie.split(","):
                if cookie.strip():
                    unique_cookies.add(cookie.strip())

        consent_data = json.loads(request.COOKIES.get(settings.SHUUP_GDPR_CONSENT_COOKIE_NAME))
        consented_cookies = set(list(consent_data.get("cookies") or []))

        # the snippet can be only injected if the user consented to all cookies
        if unique_cookies & consented_cookies == unique_cookies:
            return False

        return True
