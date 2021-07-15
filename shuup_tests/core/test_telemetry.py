# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import json
import pytest
import requests
from django.test.utils import override_settings
from django.utils.timezone import now
from mock import patch
from requests.models import Response

from shuup.admin.modules.system import SystemModule
from shuup.admin.views.dashboard import DashboardView
from shuup.core.models import PersistentCacheEntry
from shuup.core.telemetry import (
    INSTALLATION_KEY_KWARGS,
    LAST_DATA_KWARGS,
    TelemetryNotSent,
    get_daily_data,
    get_daily_data_for_day,
    get_installation_key,
    get_last_submission_time,
    get_telemetry_data,
    is_opt_out,
    set_opt_out,
    try_send_telemetry,
)
from shuup.testing.factories import (
    UserFactory,
    create_empty_order,
    create_order_with_product,
    create_product,
    create_random_company,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import SmartClient


class MockResponse(Response):
    def __init__(self, content):
        self.content = content
        super(MockResponse, self).__init__()

    def content(self):
        return self.content


def _backdate_installation_key(days=24):
    get_installation_key()
    PersistentCacheEntry.objects.filter(**INSTALLATION_KEY_KWARGS).update(time=now() - datetime.timedelta(days=days))


def _backdate_telemetry_submission(days=24):
    PersistentCacheEntry.objects.filter(**LAST_DATA_KWARGS).update(time=now() - datetime.timedelta(days=days))


def _clear_telemetry_submission():
    PersistentCacheEntry.objects.filter(**LAST_DATA_KWARGS).delete()


@pytest.mark.django_db
def test_get_telemetry_data(rf, admin_user):
    data = json.loads(get_telemetry_data(rf.get("/")))
    assert data.get("host")
    assert data.get("admin_user") == admin_user.email
    assert not json.loads(get_telemetry_data(None)).get("host")


@pytest.mark.django_db
def test_get_telemetry_data_after_login(rf, admin_user):
    get_default_shop()
    # create users to ensure correct admin is found
    UserFactory()
    UserFactory()

    data = json.loads(get_telemetry_data(rf.get("/")))
    assert data.get("admin_user") == admin_user.email
    assert not data.get("last_login")

    client = SmartClient()
    client.login(username="admin", password="password")

    data = json.loads(get_telemetry_data(rf.get("/")))
    assert data.get("admin_user") == admin_user.email
    last_login = data.get("last_login", None)
    assert last_login

    last_login_datetime = datetime.datetime.strptime(last_login, "%Y-%m-%dT%H:%M:%S.%fZ")
    today = datetime.datetime.now()
    assert last_login_datetime.year == today.year
    assert last_login_datetime.month == today.month
    assert last_login_datetime.day == today.day


@pytest.mark.django_db
def test_optin_optout(rf, admin_user):
    with override_settings(SHUUP_TELEMETRY_ENABLED=True, DEBUG=True):
        with patch.object(requests, "post", return_value=MockResponse("test")) as requestor:
            _clear_telemetry_submission()
            assert not set_opt_out(False)  # Not opted out
            assert not is_opt_out()
            try_send_telemetry()
            with pytest.raises(TelemetryNotSent) as ei:
                try_send_telemetry(raise_on_error=True)  # Still gracey
            assert ei.value.code == "grace"

            _backdate_installation_key()
            try_send_telemetry(max_age_hours=72)
            try_send_telemetry(max_age_hours=None)  # Forcibly re-send for the hell of it
            with pytest.raises(TelemetryNotSent) as ei:
                try_send_telemetry(raise_on_error=True)  # Don't ignore last-send; shouldn't send anyway
            assert ei.value.code == "age"

            assert len(requestor.mock_calls) == 2
            assert set_opt_out(True)
            assert is_opt_out()
            with pytest.raises(TelemetryNotSent) as ei:
                try_send_telemetry(max_age_hours=0, raise_on_error=True)
            assert ei.value.code == "optout"
            assert len(requestor.mock_calls) == 2


@pytest.mark.django_db
def test_disable(rf, admin_user):
    with override_settings(SHUUP_TELEMETRY_ENABLED=False):
        _clear_telemetry_submission()
        _backdate_installation_key()
        set_opt_out(False)
        with pytest.raises(TelemetryNotSent) as ei:
            try_send_telemetry(raise_on_error=True, max_age_hours=None)  # Should re-send (if we weren't disabled)
        assert ei.value.code == "disabled"


@pytest.mark.django_db
def test_graceful_error(admin_user):
    def thrower(*args, **kwargs):
        raise ValueError("Error! aaaagh")

    with override_settings(SHUUP_TELEMETRY_ENABLED=True):
        with patch.object(requests, "post", thrower) as requestor:
            _clear_telemetry_submission()
            _backdate_installation_key()
            set_opt_out(False)
            assert try_send_telemetry(raise_on_error=True).get("error")


def test_disabling_telemetry_hides_menu_item(rf):
    request = rf.get("/")
    with override_settings(SHUUP_TELEMETRY_ENABLED=True):
        assert any(me.original_url == "shuup_admin:telemetry" for me in SystemModule().get_menu_entries(request))
    with override_settings(SHUUP_TELEMETRY_ENABLED=False):
        assert not any(me.original_url == "shuup_admin:telemetry" for me in SystemModule().get_menu_entries(request))


@pytest.mark.django_db
def test_telemetry_is_sent_on_login(rf, admin_user):
    shop = get_default_shop()
    with patch.object(requests, "post", return_value=MockResponse("test")) as requestor:
        with override_settings(SHUUP_TELEMETRY_ENABLED=True):
            _backdate_installation_key(days=0)  # instance was created today
            request = apply_request_middleware(rf.get("/"), user=admin_user)
            view_func = DashboardView.as_view()
            response = view_func(request)
            sent = get_last_submission_time()

            response = view_func(request)
            assert get_last_submission_time() == sent

            response = view_func(request)
            assert get_last_submission_time() == sent

            assert len(requestor.mock_calls) == 1


def _create_order_for_day(shop, day):
    order = create_empty_order(shop=shop)
    order.order_date = day
    order.save()


def _create_product_for_day(shop, day):
    product = create_product("test_product")
    product.created_on = day
    product.save()


def _create_customer_for_day(shop, day):
    company = create_random_company()
    company.created_on = day
    company.save()


def _create_total_sales(shop, day):
    product = create_product("test", shop=shop)
    supplier = get_default_supplier()
    order = create_order_with_product(product, supplier, 1, 10, shop=shop)
    order.order_date = day
    order.save()


def _create_total_paid_sales(shop, day):
    product = create_product("test", shop=shop)
    supplier = get_default_supplier()
    order = create_order_with_product(product, supplier, 1, 10, shop=shop)
    order.order_date = day
    order.save()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()


@pytest.mark.parametrize(
    "data_key, data_value, create_object",
    [
        ("orders", 1, _create_order_for_day),
        ("products", 1, _create_product_for_day),
        ("contacts", 1, _create_customer_for_day),
        ("total_sales", 10, _create_total_sales),
        ("total_paid_sales", 10, _create_total_paid_sales),
    ],
)
@pytest.mark.django_db
def test_telemetry_daily_data_components(data_key, data_value, create_object):
    shop = get_default_shop()
    datetime_now = now()
    today = datetime.date(datetime_now.year, datetime_now.month, datetime_now.day)
    create_object(shop, today)
    assert get_daily_data_for_day(today)[data_key] == data_value


@pytest.mark.django_db
def test_telemetry_multiple_days(rf, admin_user):
    with override_settings(SHUUP_TELEMETRY_ENABLED=True, DEBUG=True):
        with patch.object(requests, "post", return_value=MockResponse("test")) as requestor:
            try_send_telemetry()
            day = now()
            _backdate_telemetry_submission(days=0)
            assert not get_daily_data(day)
            _backdate_telemetry_submission(days=20)
            assert len(get_daily_data(now())) == 19  # Since current day is not added to telemetry
