# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import activate

from shuup.gdpr.views import GDPRDownloadDataView
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def test_data_download(rf):
    activate("en")
    shop = factories.get_default_shop()
    user = factories.create_random_user()

    view = GDPRDownloadDataView.as_view()

    request = apply_request_middleware(rf.post("/"), user=user, shop=shop)
    response = view(request=request)
    assert response.status_code == 200

    request = apply_request_middleware(rf.post("/"), shop=shop)
    response = view(request=request)
    assert response.status_code == 404
