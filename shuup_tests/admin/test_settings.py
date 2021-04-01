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
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


def set_reference_method(rf, admin_user, reference_method, shop=None):
    if not shop:
        shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = SystemSettingsView.as_view()
    response = view_func(request)
    assert response.status_code == 200

    data = {"order_settings-order_reference_number_method": reference_method.value}
    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    view_func(request)
    assert configuration.get(None, consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD) == reference_method.value
    return shop


def assert_config_value(rf, admin_user, form_id, key, value, expected_value, shop=None):
    if not shop:
        shop = get_default_shop()

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = SystemSettingsView.as_view()
    response = view_func(request)
    assert response.status_code == 200

    form_field = "%s-%s" % (form_id, key)
    data = {form_field: value}
    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    response = view_func(request)
    assert response.status_code == 302
    if expected_value == "unset":
        expected_value = value
    assert configuration.get(None, key) == expected_value

    assert len(messages.get_messages(request)) == 1

    # Double save the form and the configuration should still be unchanged
    response = view_func(request)
    assert response.status_code == 302
    assert configuration.get(None, key) == expected_value

    assert len(messages.get_messages(request)) == 2

    return shop


@pytest.mark.django_db
@pytest.mark.parametrize(
    "form_id,field,value,expected_value,shop",
    [
        (
            "order_settings",
            consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD,
            OrderReferenceNumberMethod.UNIQUE.value,
            "unset",
            None,
        ),
    ],
)
def test_system_settings(rf, admin_user, form_id, field, value, expected_value, shop):
    assert_config_value(rf, admin_user, form_id, field, value, expected_value, shop)
