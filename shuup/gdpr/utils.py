# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.conf import settings
from django.template import loader
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from shuup.utils.i18n import format_datetime


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


def create_initial_privacy_policy_page(shop):
    from shuup.simple_cms.models import Page, PageType
    gdpr_document = Page.objects.filter(shop=shop, page_type=PageType.GDPR_CONSENT_DOCUMENT).first()

    if not gdpr_document:
        now_date = now()
        company_name = (shop.public_name or shop.name)
        address = shop.contact_address
        full_address = ", ".join([item for item in [
            company_name,
            address.street,
            address.city,
            address.region_code,
            address.postal_code,
            address.country.code
        ] if item])
        context = {
            "last_updated": format_datetime(now(), "LLLL dd, YYYY").capitalize(),
            "company_name": company_name,
            "full_address": full_address,
            "store_email": address.email
        }
        content = loader.render_to_string(
            template_name="shuup/admin/gdpr/privacy_policy_page.jinja",
            context=context
        )
        gdpr_document = Page.objects.create(
            shop=shop,
            page_type=PageType.GDPR_CONSENT_DOCUMENT,
            content=content,
            available_from=now_date,
            title=_("Privacy Policy"),
            url=_("privacy-policy")
        )

    return gdpr_document


def create_initial_required_cookie_category(shop):
    from shuup.gdpr.models import GDPRCookieCategory
    if not GDPRCookieCategory.objects.filter(shop=shop).exists():
        GDPRCookieCategory.objects.create(
            shop=shop,
            always_active=True,
            cookies="sessionid,csrftoken,shuup_gdpr_consent,rvp",
            name=_("Required"),
            how_is_used=_(
                "We use these cookies to ensure the correct language is being "
                "chosen for you based on your region as well as the overall site functionality."
            )
        )
