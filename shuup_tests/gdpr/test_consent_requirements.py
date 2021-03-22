# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import reversion
from django.utils.timezone import now
from django.utils.translation import activate

from shuup.gdpr.models import GDPRSettings, GDPRUserConsent
from shuup.gdpr.utils import (
    create_user_consent_for_all_documents,
    ensure_gdpr_privacy_policy,
    get_active_consent_pages,
    get_possible_consent_pages,
    get_privacy_policy_page,
    is_documents_consent_in_sync,
    should_reconsent_privacy_policy,
)
from shuup.simple_cms.models import Page
from shuup.testing import factories


def test_consent_required(rf):
    activate("en")
    shop = factories.get_default_shop()
    user = factories.create_random_user()
    page = ensure_gdpr_privacy_policy(shop)
    assert page

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    assert not gdpr_settings.enabled
    assert gdpr_settings.privacy_policy_page == page

    assert not should_reconsent_privacy_policy(shop, user)
    assert is_documents_consent_in_sync(shop, user)  # settings not enabled

    assert page in get_possible_consent_pages(shop)

    # enable gpdr
    gdpr_settings.enabled = True
    gdpr_settings.save()
    assert gdpr_settings.privacy_policy_page == get_privacy_policy_page(shop)
    assert not is_documents_consent_in_sync(shop, user)

    # create revisioned page
    hidden_page = Page.objects.create(shop=shop, available_from=None)
    assert hidden_page not in Page.objects.visible(shop=shop)
    assert gdpr_settings.privacy_policy_page == get_privacy_policy_page(shop)
    assert hidden_page in get_possible_consent_pages(shop)

    with reversion.create_revision():
        page.save()

    create_user_consent_for_all_documents(shop, user)
    assert GDPRUserConsent.objects.filter(user=user, shop=shop).count() == 1

    consent = GDPRUserConsent.objects.get(user=user, shop=shop)

    pages = [c.page for c in consent.documents.all()]
    assert page in pages
    assert hidden_page not in pages  # not there due not visible

    with reversion.create_revision():
        page.save()

    # add a new (visible) page
    available_page = Page.objects.create(shop=shop, available_from=now())
    assert available_page in Page.objects.visible(shop=shop)

    create_user_consent_for_all_documents(shop, user)
    consent = GDPRUserConsent.objects.get(user=user, shop=shop)

    pages = [c.page for c in consent.documents.all()]
    assert page in pages
    assert hidden_page not in pages  # not there due not visible
    assert available_page not in pages  # not there due defined in settings
    assert available_page in get_possible_consent_pages(shop)
    assert available_page not in get_active_consent_pages(shop)

    gdpr_settings.consent_pages.add(available_page)
    gdpr_settings.refresh_from_db()
    assert gdpr_settings.privacy_policy_page
    assert gdpr_settings.consent_pages.count() == 1

    assert available_page in get_active_consent_pages(shop)

    assert consent.documents.count() == 1
    create_user_consent_for_all_documents(shop, user)
    consent = GDPRUserConsent.objects.get(user=user, shop=shop)
    assert consent.documents.count() == 2

    assert is_documents_consent_in_sync(shop, user)

    pages = [c.page for c in consent.documents.all()]
    assert page in pages
    assert hidden_page not in pages  # not there due not visible
    assert available_page in pages
