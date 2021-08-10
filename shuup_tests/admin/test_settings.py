# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib import messages
from django.db import models

from shuup import configuration
from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod
from shuup.admin.modules.settings.forms.system import CoreSettingsForm, OrderSettingsForm
from shuup.admin.modules.settings.views import SystemSettingsView
from shuup.core.models import Currency
from shuup.core.setting_keys import (
    SHUUP_ADDRESS_HOME_COUNTRY,
    SHUUP_ALLOW_ANONYMOUS_ORDERS,
    SHUUP_DISCOUNT_MODULES,
    SHUUP_HOME_CURRENCY,
    SHUUP_PRICING_MODULE,
    SHUUP_REFERENCE_NUMBER_LENGTH,
    SHUUP_REFERENCE_NUMBER_METHOD,
    SHUUP_REFERENCE_NUMBER_PREFIX,
)
from shuup.testing.utils import apply_request_middleware


def get_data(reference_method):
    return {
        (
            "order_settings",
            SHUUP_REFERENCE_NUMBER_METHOD,
            reference_method.value,
            reference_method.value,
        ),
        (
            "order_settings",
            SHUUP_REFERENCE_NUMBER_LENGTH,
            17,
            17,
        ),
        (
            "order_settings",
            SHUUP_REFERENCE_NUMBER_PREFIX,
            "",
            "",
        ),
        (
            "order_settings",
            SHUUP_DISCOUNT_MODULES,
            ("customer_group_discount", "product_discounts"),
            ("customer_group_discount", "product_discounts"),
        ),
        (
            "order_settings",
            SHUUP_PRICING_MODULE,
            "multivendor_supplier_pricing",
            "multivendor_supplier_pricing",
        ),
        (
            "order_settings",
            SHUUP_ALLOW_ANONYMOUS_ORDERS,
            True,
            True,
        ),
        ("core_settings", SHUUP_HOME_CURRENCY, Currency.objects.all().first().id, Currency.objects.all().first().code),
        (
            "core_settings",
            SHUUP_ADDRESS_HOME_COUNTRY,
            "US",
            "US",
        ),
    }


def get_settings_data(field_data, format=None):
    data_dict = {}
    for form_id, key, value, expected_value in field_data:
        if format == "form":
            form_field = "%s" % (key)
        else:
            form_field = "%s-%s" % (form_id, key)
        data_dict.update(
            {
                form_field: value,
            }
        )
    return data_dict


@pytest.mark.django_db
def test_system_settings_forms(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    field_data = get_data(OrderReferenceNumberMethod.UNIQUE)

    order_form = OrderSettingsForm(request=request, data=get_settings_data(field_data, "form"))
    result = order_form.is_valid()
    assert result is True
    cleaned_data = dict()
    cleaned_data.update(order_form.cleaned_data)

    core_form = CoreSettingsForm(request=request, data=get_settings_data(field_data, "form"))
    result = core_form.is_valid()
    assert result is True
    cleaned_data.update(core_form.cleaned_data)

    for form_id, key, value, expected_value in field_data:
        if isinstance(cleaned_data[key], (str, int, bool)):
            assert cleaned_data[key] == expected_value
        elif isinstance(cleaned_data[key], list):
            assert cleaned_data[key] == list(expected_value)
        else:
            assert str(cleaned_data[key]) == expected_value


@pytest.mark.parametrize(
    "reference_method",
    [OrderReferenceNumberMethod.UNIQUE, OrderReferenceNumberMethod.RUNNING, OrderReferenceNumberMethod.SHOP_RUNNING],
)
@pytest.mark.django_db
def test_system_settings(rf, admin_user, reference_method):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = SystemSettingsView.as_view()
    response = view_func(request)
    assert response.status_code == 200

    field_data = get_data(reference_method)
    data = get_settings_data(field_data)
    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    response = view_func(request)

    assert response.status_code == 302
    for form_id, key, value, expected_value in field_data:
        result_value = configuration.get(None, key)
        if isinstance(expected_value, models.Model):
            assert result_value == str(expected_value)
        elif isinstance(result_value, list):
            assert result_value == list(expected_value)
        else:
            assert result_value == expected_value

    assert len(messages.get_messages(request)) == 1

    # Double save the form and the configuration should still be unchanged
    response = view_func(request)
    assert response.status_code == 302
    for form_id, key, value, expected_value in field_data:
        result_value = configuration.get(None, key)
        if isinstance(expected_value, models.Model):
            assert configuration.get(None, key) == str(expected_value)
        elif isinstance(result_value, list):
            assert result_value == list(expected_value)
        else:
            assert configuration.get(None, key) == expected_value

    assert len(messages.get_messages(request)) == 2
