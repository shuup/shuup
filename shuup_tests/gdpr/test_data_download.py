# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
from django.utils.translation import activate

from shuup.gdpr.models import GDPRSettings, GDPRUserConsent
from shuup.gdpr.utils import create_user_consent_for_all_documents, ensure_gdpr_privacy_policy
from shuup.gdpr.views import GDPRDownloadDataView
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def test_data_download(rf):
    activate("en")
    shop = factories.get_default_shop()
    user = factories.create_random_user()

    page = ensure_gdpr_privacy_policy(shop)
    assert page
    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.save()
    assert gdpr_settings.privacy_policy_page == page
    create_user_consent_for_all_documents(shop, user)

    view = GDPRDownloadDataView.as_view()

    request = apply_request_middleware(rf.post("/"), user=user, shop=shop)
    response = view(request=request)
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))

    assert data == {}

    request = apply_request_middleware(rf.post("/"), shop=shop)
    response = view(request=request)
    assert response.status_code == 404
