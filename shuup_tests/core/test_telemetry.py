# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
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
from shuup.core.models import PersistentCacheEntry
from shuup.core.telemetry import (
    get_installation_key, get_telemetry_data, INSTALLATION_KEY_KWARGS,
    is_opt_out, LAST_DATA_KWARGS, set_opt_out, TelemetryNotSent,
    try_send_telemetry
)


def _backdate_installation_key():
    get_installation_key()
    PersistentCacheEntry.objects.filter(**INSTALLATION_KEY_KWARGS).update(time=now() - datetime.timedelta(days=24))


def _clear_telemetry_submission():
    PersistentCacheEntry.objects.filter(**LAST_DATA_KWARGS).delete()


@pytest.mark.django_db
def test_get_telemetry_data(rf):
    assert json.loads(get_telemetry_data(rf.get("/"))).get("host")
    assert not json.loads(get_telemetry_data(None)).get("host")


@pytest.mark.django_db
def test_optin_optout(rf):
    with override_settings(SHUUP_TELEMETRY_ENABLED=True):
        with patch.object(requests, "post", return_value=Response()) as requestor:
            _clear_telemetry_submission()
            assert not set_opt_out(False)  # Not opted out
            assert not is_opt_out()
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
            _clear_telemetry_submission()
            with pytest.raises(TelemetryNotSent) as ei:
                try_send_telemetry(max_age_hours=0, raise_on_error=True)
            assert ei.value.code == "optout"
            assert len(requestor.mock_calls) == 2


@pytest.mark.django_db
def test_disable(rf):
    with override_settings(SHUUP_TELEMETRY_ENABLED=False):
        _clear_telemetry_submission()
        _backdate_installation_key()
        set_opt_out(False)
        with pytest.raises(TelemetryNotSent) as ei:
            try_send_telemetry(raise_on_error=True, max_age_hours=None)  # Should re-send (if we weren't disabled)
        assert ei.value.code == "disabled"


@pytest.mark.django_db
def test_graceful_error():
    def thrower(*args, **kwargs):
        raise ValueError("aaaagh")

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
