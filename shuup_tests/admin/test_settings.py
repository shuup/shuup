# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup import configuration
from shuup.admin.modules.settings import consts
from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod
from shuup.core.models import ConfigurationItem
from shuup.testing.factories import get_default_shop

from shuup.admin.modules.settings.views import SystemSettingsView
from shuup.testing.utils import apply_request_middleware


def set_reference_method(rf, admin_user, reference_method, shop=None):
    if not shop:
        shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = SystemSettingsView.as_view()
    response = view_func(request)
    assert response.status_code == 200

    data = {
        "order_reference_number_method": reference_method.value
    }
    request = apply_request_middleware(rf.post("/", data=data))
    view_func(request)
    assert configuration.get(None, consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD) == reference_method.value
    return shop


@pytest.mark.django_db
def test_system_settings(rf, admin_user):
    set_reference_method(rf, admin_user, OrderReferenceNumberMethod.UNIQUE)
