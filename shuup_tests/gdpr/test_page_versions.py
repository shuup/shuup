# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings
from django.utils.translation import activate
from reversion.models import Version

from shuup.gdpr.models import GDPRSettings, GDPRUserConsent, GDPRUserConsentDocument
from shuup.gdpr.utils import (
    create_user_consent_for_all_documents,
    ensure_gdpr_privacy_policy,
    is_documents_consent_in_sync,
)
from shuup.simple_cms.admin_module.views import PageEditView
from shuup.simple_cms.models import Page
from shuup.testing import factories
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_page_form(rf, admin_user):
    with override_settings(LANGUAGES=[("en", "en")]):
        activate("en")
        shop = get_default_shop()
        gdpr_settings = GDPRSettings.get_for_shop(shop)
        gdpr_settings.enabled = True
        gdpr_settings.save()

        original_gdpr_page = ensure_gdpr_privacy_policy(shop)
        versions = Version.objects.get_for_object(original_gdpr_page)
        assert len(versions) == 1

        # consent to this with user
        user = factories.create_random_user("en")
        assert not GDPRUserConsent.objects.filter(shop=shop, user=user).exists()
        original_consent = create_user_consent_for_all_documents(shop, user)

        assert GDPRUserConsent.objects.filter(shop=shop, user=user).count() == 1

        # create one outside the usual flow
        GDPRUserConsent.objects.create(user=user, shop=shop)
        assert GDPRUserConsent.objects.filter(shop=shop, user=user).count() == 2

        # consent again
        new_consent = create_user_consent_for_all_documents(shop, user)
        assert GDPRUserConsent.objects.filter(shop=shop, user=user).count() == 1
        assert original_consent.pk == new_consent.pk

        version = versions[0]
        assert GDPRUserConsentDocument.objects.filter(page=original_gdpr_page, version=version).exists()

        assert is_documents_consent_in_sync(shop, user)

        assert Page.objects.count() == 1

        view = PageEditView.as_view()

        # load the page
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        response = view(request, pk=original_gdpr_page.pk)
        assert 200 <= response.status_code < 300

        # update the page
        post_data = {
            "base-content__en": "test_data",
            "base-available_from": "",
            "base-url__en": "test",
            "base-title__en": "defa",
            "base-available_to": "",
        }
        request = apply_request_middleware(rf.post("/", post_data), user=admin_user)
        response = view(request, pk=original_gdpr_page.pk)
        if hasattr(response, "render"):
            content = response.render()
        assert response.status_code in [200, 302]

        versions = Version.objects.get_for_object(original_gdpr_page)
        assert len(versions) == 4  # saved 4 times in total

        assert not is_documents_consent_in_sync(shop, user)

        create_user_consent_for_all_documents(shop, user)
        assert is_documents_consent_in_sync(shop, user)
