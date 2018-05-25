# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.conf import settings


def get_consent_from_cookie(cookie_data):
    """
    Returns a tuple of (consent_cookies, consent_cookie_categories, consent_documents)
    read from the cookie data (dictionary)

    :param cookie_data dict: the dictionary parsed from cookie
    """
    from shuup.gdpr.models import GDPRCookieCategory
    from shuup.simple_cms.models import Page
    consent_cookies = cookie_data.get("cookies", [])
    consent_cookie_categories = GDPRCookieCategory.objects.filter(id__in=cookie_data.get("cookie_categories", []))
    documents_ids = [doc["id"] for doc in cookie_data.get("consent_documents", [])]
    consent_documents = Page.objects.filter(id__in=documents_ids)
    return (consent_cookies, consent_cookie_categories, consent_documents)


def add_consent_to_response_cookie(response, cookie_data):
    response.set_cookie(
        key=settings.SHUUP_GDPR_CONSENT_COOKIE_NAME,
        value=json.dumps(cookie_data),
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None
    )


def get_cookie_consent_data(consent_cookie_categories, consent_documents, consent_cookies=[]):
    """
    :param list[GDPRCookieCategory] consent_cookie_categories: list of cookie category
    :param list[simple_cms.Page] consent_documents: list of documents to
    :param list[str] consent_cookies: list of consent cookie names, if not set,
        if will be generated from consent_cookie_categories
    """
    if not consent_cookies:
        consent_cookies = [cookie_category.cookies for cookie_category in consent_cookie_categories]
        consent_cookies = list(set(",".join(consent_cookies).replace(" ", "").split(",")))
    return {
        "cookies": consent_cookies,
        "cookie_categories": [cookie_category.id for cookie_category in consent_cookie_categories],
        "documents": [
            dict(url=consent_document.url, id=consent_document.id)
            for consent_document in consent_documents
        ]
    }


def get_all_contact_data(contact):
    from shuup.core.models import CompanyContact
    from shuup.gdpr.serializers import GDPRCompanyContactSerializer, GDPRPersonContactSerializer

    if isinstance(contact, CompanyContact):
        return GDPRCompanyContactSerializer(contact).data

    return GDPRPersonContactSerializer(contact).data
