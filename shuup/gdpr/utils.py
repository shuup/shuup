# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
from datetime import timedelta
from django.conf import settings
from django.template import loader
from django.utils.timezone import now
from django.utils.translation import activate, get_language, ugettext_lazy as _
from reversion import create_revision

from shuup.simple_cms.models import Page
from shuup.utils.django_compat import force_text
from shuup.utils.i18n import format_datetime


def add_consent_to_response_cookie(response, cookie_data):
    response.set_cookie(
        key=settings.SHUUP_GDPR_CONSENT_COOKIE_NAME,
        value=json.dumps(cookie_data),
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,
        expires=now() + timedelta(days=365 * 3),
    )


def get_cookie_consent_data(cookie_categories, consent_documents):
    """
    :param list[GDPRCookieCategory] cookie_categories: list of cookie category
    """
    consent_cookies = [cookie_category.cookies for cookie_category in cookie_categories]
    return {
        "cookies": list(set(",".join(consent_cookies).replace(" ", "").split(","))),
        "documents": [dict(id=doc.id, url=doc.url) for doc in consent_documents],
    }


def get_all_contact_data(contact):
    from shuup.core.models import CompanyContact
    from shuup.gdpr.serializers import GDPRCompanyContactSerializer, GDPRPersonContactSerializer

    if isinstance(contact, CompanyContact):
        return GDPRCompanyContactSerializer(contact).data
    return GDPRPersonContactSerializer(contact).data


def ensure_gdpr_privacy_policy(shop, force_update=False):
    from shuup.gdpr.models import GDPRSettings
    from shuup.simple_cms.models import Page

    gdpr_document = get_privacy_policy_page(shop)
    current_language = get_language()

    if force_update or not gdpr_document:
        now_date = now()
        company_name = shop.public_name or shop.name
        address = shop.contact_address
        full_address = ""
        if address:
            full_address = ", ".join(
                [
                    item
                    for item in [
                        company_name,
                        address.street,
                        address.city,
                        address.region_code,
                        address.postal_code,
                        address.country.code,
                    ]
                    if item
                ]
            )
        context = {
            "last_updated": format_datetime(now(), "LLLL dd, YYYY").capitalize(),
            "company_name": company_name,
            "full_address": full_address,
            "store_email": address.email if address else "",
        }
        content = loader.render_to_string(template_name="shuup/admin/gdpr/privacy_policy_page.jinja", context=context)
        created = False
        if not gdpr_document:
            with create_revision():
                gdpr_document = Page.objects.create(
                    shop=shop,
                    content=content,
                    available_from=now_date,
                    title=force_text(_("Privacy Policy")),
                    url=settings.GDPR_PRIVACY_POLICY_PAGE_URLS.get(current_language, "privacy-policy"),
                )
                created = True
            gdpr_settings = GDPRSettings.get_for_shop(shop)
            gdpr_settings.privacy_policy_page = gdpr_document
            gdpr_settings.save()

        # update only if it was created
        if created or force_update:
            for code, language in settings.LANGUAGES:
                if code == current_language:
                    continue
                url = settings.GDPR_PRIVACY_POLICY_PAGE_URLS.get(code)
                if not url:
                    continue

                activate(code)
                content = loader.render_to_string(
                    template_name="shuup/admin/gdpr/privacy_policy_page.jinja", context=context
                )
                gdpr_document.set_current_language(code)
                gdpr_document.title = force_text(_("Privacy Policy"))
                gdpr_document.url = url
                gdpr_document.content = content
                gdpr_document.save()

    # return to old language
    activate(current_language)
    gdpr_document.set_current_language(current_language)
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
            ),
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
        cookie_category.set_current_language(current_language)


def should_reconsent_privacy_policy(shop, user):
    from shuup.gdpr.models import GDPRUserConsent

    consent = GDPRUserConsent.objects.filter(shop=shop, user=user).first()
    if not consent:
        return False
    privacy_policy = get_privacy_policy_page(shop)
    if not privacy_policy:
        return False
    return consent.should_reconsent_to_page(privacy_policy)


def is_documents_consent_in_sync(shop, user):
    """
    Returns whether the user has consent to the lastest document versions
    """
    from shuup.gdpr.models import GDPRSettings

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    if not gdpr_settings.enabled:
        return True  # nothing to do.

    from shuup.gdpr.models import GDPRUserConsent

    last_user_consent = GDPRUserConsent.get_for_user(user, shop)
    if not last_user_consent:
        return False
    return not last_user_consent.should_reconsent(shop, user)


def create_user_consent_for_all_documents(shop, user):
    """
    Create user consent for all available GDPR documents
    """
    from shuup.gdpr.models import GDPRSettings, GDPRUserConsent

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    if not gdpr_settings.enabled or is_documents_consent_in_sync(shop, user):
        return

    consent_documents = get_active_consent_pages(shop)
    return GDPRUserConsent.ensure_for_user(user, shop, consent_documents)


def get_possible_consent_pages(shop):
    return Page.objects.filter(shop=shop, deleted=False)


def get_active_consent_pages(shop):
    from shuup.gdpr.models import GDPRSettings

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    if not gdpr_settings.enabled:
        return []  # nothing to do.
    ids = [page.id for page in gdpr_settings.consent_pages.all()]
    if gdpr_settings.privacy_policy_page:
        ids.append(gdpr_settings.privacy_policy_page.pk)
    return Page.objects.filter(pk__in=set(ids))


def get_privacy_policy_page(shop):
    from shuup.gdpr.models import GDPRSettings

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    if not gdpr_settings.enabled:
        return None
    return gdpr_settings.privacy_policy_page
