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
from shuup.admin.modules.settings.views import SystemSettingsView
from shuup.admin.setting_keys import (
    SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION,
    SHUUP_ADMIN_ALLOW_HTML_IN_SUPPLIER_DESCRIPTION,
)
from shuup.core.constants import DEFAULT_REFERENCE_NUMBER_LENGTH
from shuup.core.models import Currency
from shuup.core.setting_keys import (
    SHUUP_ADDRESS_HOME_COUNTRY,
    SHUUP_ALLOW_ANONYMOUS_ORDERS,
    SHUUP_ALLOWED_UPLOAD_EXTENSIONS,
    SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE,
    SHUUP_DEFAULT_ORDER_LABEL,
    SHUUP_DISCOUNT_MODULES,
    SHUUP_ENABLE_ATTRIBUTES,
    SHUUP_ENABLE_MULTIPLE_SHOPS,
    SHUUP_ENABLE_MULTIPLE_SUPPLIERS,
    SHUUP_HOME_CURRENCY,
    SHUUP_LENGTH_UNIT,
    SHUUP_MANAGE_CONTACTS_PER_SHOP,
    SHUUP_MASS_UNIT,
    SHUUP_ORDER_SOURCE_MODIFIER_MODULES,
    SHUUP_PRICING_MODULE,
    SHUUP_REFERENCE_NUMBER_LENGTH,
    SHUUP_REFERENCE_NUMBER_METHOD,
    SHUUP_REFERENCE_NUMBER_PREFIX,
    SHUUP_TAX_MODULE,
    SHUUP_TELEMETRY_ENABLED,
    SHUUP_VOLUME_UNIT,
)
from shuup.front.setting_keys import SHUUP_FRONT_MAX_UPLOAD_SIZE
from shuup.reports.constants import DEFAULT_REPORTS_ITEM_LIMIT
from shuup.reports.setting_keys import SHUUP_DEFAULT_REPORTS_ITEM_LIMIT
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
            DEFAULT_REFERENCE_NUMBER_LENGTH,
            DEFAULT_REFERENCE_NUMBER_LENGTH,
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
            "customer_group_pricing",
            "customer_group_pricing",
        ),
        (
            "order_settings",
            SHUUP_ALLOW_ANONYMOUS_ORDERS,
            True,
            True,
        ),
        (
            "order_settings",
            SHUUP_ORDER_SOURCE_MODIFIER_MODULES,
            ("basket_campaigns"),
            ("basket_campaigns"),
        ),
        (
            "order_settings",
            SHUUP_DEFAULT_ORDER_LABEL,
            "default",
            "default",
        ),
        ("core_settings", SHUUP_HOME_CURRENCY, Currency.objects.all().first().id, Currency.objects.all().first().code),
        (
            "core_settings",
            SHUUP_ADDRESS_HOME_COUNTRY,
            "US",
            "US",
        ),
        (
            "core_settings",
            SHUUP_TAX_MODULE,
            "default_tax",
            "default_tax",
        ),
        (
            "core_settings",
            SHUUP_ENABLE_ATTRIBUTES,
            True,
            True,
        ),
        (
            "core_settings",
            SHUUP_ENABLE_MULTIPLE_SHOPS,
            False,
            False,
        ),
        (
            "core_settings",
            SHUUP_ENABLE_MULTIPLE_SUPPLIERS,
            False,
            False,
        ),
        (
            "core_settings",
            SHUUP_MANAGE_CONTACTS_PER_SHOP,
            False,
            False,
        ),
        (
            "core_settings",
            SHUUP_TELEMETRY_ENABLED,
            False,
            False,
        ),
        (
            "core_settings",
            SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE,
            True,
            True,
        ),
        (
            "core_settings",
            SHUUP_ALLOWED_UPLOAD_EXTENSIONS,
            ("pdf,ttf,eot,woff,woff2,otf"),
            ("pdf", "ttf", "eot", "woff", "woff2", "otf"),
        ),
        (
            "core_settings",
            SHUUP_MASS_UNIT,
            "g",
            "g",
        ),
        (
            "core_settings",
            SHUUP_LENGTH_UNIT,
            "mm",
            "mm",
        ),
        (
            "core_settings",
            SHUUP_VOLUME_UNIT,
            "mm3",
            "mm3",
        ),
        (
            "admin_settings",
            SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION,
            True,
            True,
        ),
        (
            "admin_settings",
            SHUUP_ADMIN_ALLOW_HTML_IN_SUPPLIER_DESCRIPTION,
            True,
            True,
        ),
        (
            "front_settings",
            SHUUP_FRONT_MAX_UPLOAD_SIZE,
            500000,
            500000,
        ),
        (
            "report_settings",
            SHUUP_DEFAULT_REPORTS_ITEM_LIMIT,
            DEFAULT_REPORTS_ITEM_LIMIT,
            DEFAULT_REPORTS_ITEM_LIMIT,
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

    system_view = SystemSettingsView()
    form_part_classes = system_view.get_form_part_classes()
    cleaned_data = dict()
    for form_part_class in form_part_classes:
        print(form_part_class)
        form = form_part_class.form(request=request, data=get_settings_data(field_data, "form"))
        result = form.is_valid()
        assert result is True
        cleaned_data.update(form.cleaned_data)

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
