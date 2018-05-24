# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View

from shuup.gdpr.models import GDPRCookieCategory, GDPRUserConsent
from shuup.utils.djangoenv import has_installed

from .utils import get_cookie_consent_data

COOKIE_CONSENT_RE = r"cookie_category_(\d+)"


class GDPRConsentView(View):
    def post(self, request, *args, **kwargs):
        shop = request.shop
        cookie_categories = list(GDPRCookieCategory.objects.filter(shop=shop, always_active=True))

        for field, value in request.POST.items():
            field_match = re.match(COOKIE_CONSENT_RE, field)
            if field_match and value.lower() in ["on", "1"]:
                cookie_category = GDPRCookieCategory.objects.filter(shop=shop, id=field_match.groups()[0]).first()
                if cookie_category:
                    cookie_categories.append(cookie_category)

        consent_documents = []
        if has_installed("shuup.simple_cms"):
            from shuup.simple_cms.models import Page, PageType
            consent_documents = list(Page.objects.visible(shop).filter(page_type=PageType.GDPR_CONSENT_DOCUMENT))

        cookie_data = get_cookie_consent_data(cookie_categories, consent_documents)

        # create the consent for the authenticated user
        if request.user.is_authenticated():
            gdpr_user_consent = GDPRUserConsent.objects.create(
                shop=shop,
                user=request.user,
                cookies=",".join(cookie_data["cookies"])
            )
            gdpr_user_consent.documents = consent_documents
            gdpr_user_consent.cookie_categories = cookie_categories

        response = HttpResponseRedirect(reverse("shuup:index"))
        response.set_cookie(
            key=settings.SHUUP_GDPR_CONSENT_COOKIE_NAME,
            value=json.dumps(cookie_data),
            domain=settings.SESSION_COOKIE_DOMAIN,
            secure=settings.SESSION_COOKIE_SECURE or None
        )
        return response
