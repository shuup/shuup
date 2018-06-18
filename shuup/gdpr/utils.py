# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.conf import settings
from django.template import loader
from django.utils.encoding import force_text
from django.utils.timezone import now
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _

from shuup.utils.i18n import format_datetime


def get_consent_from_cookie(cookie_data):
    """
    Returns a tuple of (consent_cookies, consent_cookie_categories)
    read from the cookie data (dictionary)

    :param cookie_data dict: the dictionary parsed from cookie
    """
    from shuup.gdpr.models import GDPRCookieCategory
    consent_cookies = cookie_data.get("cookies", [])
    consent_cookie_categories = GDPRCookieCategory.objects.filter(id__in=cookie_data.get("cookie_categories", []))
    return (consent_cookies, consent_cookie_categories)


def add_consent_to_response_cookie(response, cookie_data):
    response.set_cookie(
        key=settings.SHUUP_GDPR_CONSENT_COOKIE_NAME,
        value=json.dumps(cookie_data),
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None
    )


def get_cookie_consent_data(cookie_categories, consent_documents=[]):
    """
    :param list[GDPRCookieCategory] cookie_categories: list of cookie category
    """
    consent_cookies = [cookie_category.cookies for cookie_category in cookie_categories]
    return {
        "cookies": list(set(",".join(consent_cookies).replace(" ", "").split(","))),
        "documents": [
            dict(id=doc.id, url=doc.url)
            for doc in consent_documents
        ]
    }


def get_all_contact_data(contact):
    from shuup.core.models import CompanyContact
    from shuup.gdpr.serializers import GDPRCompanyContactSerializer, GDPRPersonContactSerializer

    if isinstance(contact, CompanyContact):
        return GDPRCompanyContactSerializer(contact).data
    return GDPRPersonContactSerializer(contact).data


def ensure_gdpr_privacy_policy(shop, force_update=False):
    from shuup.simple_cms.models import Page, PageType
    gdpr_document = Page.objects.filter(shop=shop, page_type=PageType.REVISIONED).first()

    if force_update or not gdpr_document:
        now_date = now()
        company_name = (shop.public_name or shop.name)
        address = shop.contact_address
        full_address = ""
        if address:
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
            "store_email": address.email if address else ""
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
            title=force_text(_("Privacy Policy")),
            url=force_text(_("privacy-policy"))
        )
        current_language = get_language()
        for code, language in settings.LANGUAGES:
            if code == current_language:
                continue
            activate(code)
            gdpr_document.set_current_language(code)
            gdpr_document.title = force_text(_("Privacy Policy"))
            gdpr_document.url = force_text(_("privacy-policy"))
            gdpr_document.save()
        activate(current_language)

    return gdpr_document


def create_initial_required_cookie_category(shop):
    from shuup.gdpr.models import GDPRCookieCategory
    if not GDPRCookieCategory.objects.filter(shop=shop).exists():
        cookie_category = GDPRCookieCategory.objects.create(
            shop=shop,
            always_active=True,
            cookies="sessionid,csrftoken,shuup_gdpr_consent,rvp",
            name=_("Required"),
            how_is_used=_(
                "We use these cookies to ensure the correct language is being "
                "chosen for you based on your region as well as the overall site functionality."
            )
        )
        current_language = get_language()
        for code, language in settings.LANGUAGES:
            if code == current_language:
                continue
            activate(code)
            cookie_category.set_current_language(code)
            cookie_category.name = _("Required")
            cookie_category.how_is_used = _(
                "We use these cookies to ensure the correct language is being "
                "chosen for you based on your region as well as the overall site functionality."
            )
            cookie_category.save()
        activate(current_language)


def is_documents_consent_in_sync(shop, user):
    """
    Returns whether the user has consent to the lastest document versions
    """
    from shuup.gdpr.models import GDPRUserConsent
    last_user_consent = GDPRUserConsent.objects.filter(user=user, shop=shop).order_by("-created_on").first()
    if not last_user_consent:
        return False

    # get all documents user has consent
    user_consent_documents = last_user_consent.documents.all()

    from shuup.simple_cms.models import Page, PageType
    # if any of the current consent documentis not consent by user, he are not in sync
    for consent_document in Page.objects.visible(shop).filter(page_type=PageType.GDPR_CONSENT_DOCUMENT):
        if consent_document not in user_consent_documents:
            return False

    return True


def create_user_consent_for_all_documents(shop, user):
    """
    Create user consent for all available GDPR documents
    """
    from shuup.gdpr.models import GDPRUserConsent, GDPRSettings

    if not GDPRSettings.get_for_shop(shop).enabled or is_documents_consent_in_sync(shop, user):
        return

    from shuup.simple_cms.models import Page, PageType
    consent_documents = Page.objects.visible(shop).filter(page_type=PageType.REVISIONED)
    GDPRUserConsent.create_for_user(user, shop, consent_documents)
