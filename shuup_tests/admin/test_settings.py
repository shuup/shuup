# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib import messages

from shuup import configuration
from shuup.admin.modules.settings import consts
from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod
from shuup.admin.modules.settings.views import SystemSettingsView
from shuup.core.setting_keys import SHUUP_ALLOW_ANONYMOUS_ORDERS, SHUUP_HOME_CURRENCY
from shuup.testing.utils import apply_request_middleware


@pytest.mark.parametrize(
    "reference_method",
    [OrderReferenceNumberMethod.UNIQUE, OrderReferenceNumberMethod.RUNNING, OrderReferenceNumberMethod.SHOP_RUNNING],
)
@pytest.mark.django_db
def test_system_settings(rf, admin_user, reference_method):
    field_data = {
        (
            "order_settings",
            consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD,
            reference_method.value,
        ),
        (
            "order_settings",
            SHUUP_ALLOW_ANONYMOUS_ORDERS,
            True,
        ),
        (
            "core_settings",
            SHUUP_HOME_CURRENCY,
            "USD",
        ),
    }

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = SystemSettingsView.as_view()
    response = view_func(request)
    assert response.status_code == 200

    data = {}
    for form_id, key, value in field_data:
        form_field = "%s-%s" % (form_id, key)
        data.update(
            {
                form_field: value,
            }
        )
    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    response = view_func(request)

    assert response.status_code == 302
    for form_id, key, expected_value in field_data:
        assert configuration.get(None, key) == expected_value

    assert len(messages.get_messages(request)) == 1

    # Double save the form and the configuration should still be unchanged
    response = view_func(request)
    assert response.status_code == 302
    for form_id, key, expected_value in field_data:
        assert configuration.get(None, key) == expected_value

    assert len(messages.get_messages(request)) == 2
