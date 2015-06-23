# -*- coding: utf-8 -*-
from django.test.utils import override_settings
from django.utils.timezone import now
from mock import patch
from requests.models import Response
import datetime
import json
import pytest
import requests
from shoop.admin.modules.system import SystemModule

from shoop.core.models import PersistentCacheEntry
from shoop.core.telemetry import (
    get_telemetry_data, set_opt_out, try_send_telemetry, is_opt_out,
    get_installation_key, INSTALLATION_KEY_KWARGS, LAST_DATA_KWARGS,
    TelemetryNotSent)


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
    with override_settings(SHOOP_TELEMETRY_ENABLED=True):
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
    with override_settings(SHOOP_TELEMETRY_ENABLED=False):
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

    with override_settings(SHOOP_TELEMETRY_ENABLED=True):
        with patch.object(requests, "post", thrower) as requestor:
            _clear_telemetry_submission()
            _backdate_installation_key()
            set_opt_out(False)
            assert try_send_telemetry(raise_on_error=True).get("error")


