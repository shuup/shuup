# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import json
import platform
import sys

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.crypto import get_random_string
from django.utils.encoding import force_text
from django.utils.timezone import now
import requests

import shoop
from shoop.core.models import PersistentCacheEntry

OPT_OUT_KWARGS = dict(module="telemetry", key="opt_out")
INSTALLATION_KEY_KWARGS = dict(module="telemetry", key="installation_key")
LAST_DATA_KWARGS = dict(module="telemetry", key="last_data")


def safe_json(data_dict, indent=None):
    return json.dumps(data_dict, cls=DjangoJSONEncoder, sort_keys=True, indent=indent)


def get_installation_key():
    """
    Get the unique installation ID for this Shoop instance.

    If one doesn't exist, it's generated and saved at this point.

    :return: Installation key string
    :rtype: str
    """
    try:
        return PersistentCacheEntry.objects.get(**INSTALLATION_KEY_KWARGS).data
    except ObjectDoesNotExist:
        key = get_random_string(48)
        PersistentCacheEntry.objects.create(data=key, **INSTALLATION_KEY_KWARGS)
        return key


def is_opt_out():
    return PersistentCacheEntry.objects.filter(**OPT_OUT_KWARGS).exists()


def is_in_grace_period():
    """
    Return True if the telemetry module is within the 24-hours-from-installation
    grace period where no stats are sent.  This is to "safely" allow opting out
    of telemetry without leaving a trace.

    :return: Graceness flag.
    :rtype: bool
    """
    get_installation_key()  # Need to initialize here
    installation_time = PersistentCacheEntry.objects.get(**INSTALLATION_KEY_KWARGS).time
    return ((now() - installation_time).total_seconds() < 60 * 60 * 24)


def is_telemetry_enabled():
    return bool(settings.SHOOP_TELEMETRY_ENABLED)


def set_opt_out(flag):
    """
    Set whether this installation is opted-out from telemetry submissions.

    :param flag: Opt-out flag. True for opt-out, false for opt-in (default)
    :type flag: bool
    :return: New flag state
    :rtype: bool
    """
    if flag and not is_opt_out():
        PersistentCacheEntry.objects.create(data=True, **OPT_OUT_KWARGS)
        return True
    else:
        PersistentCacheEntry.objects.filter(**OPT_OUT_KWARGS).delete()
        return False


def get_last_submission_time():
    try:
        return PersistentCacheEntry.objects.get(**LAST_DATA_KWARGS).time
    except ObjectDoesNotExist:
        return None


def get_last_submission_data():
    try:
        return safe_json(PersistentCacheEntry.objects.get(**LAST_DATA_KWARGS).data, indent=4)
    except ObjectDoesNotExist:
        return None


def save_telemetry_submission(data):
    """
    Save a blob of data as the latest telemetry submission.

    Naturally updates the latest submission time.

    :param data: A blob of data.
    :type data: dict
    """
    pce, _ = PersistentCacheEntry.objects.get_or_create(defaults={"data": None}, **LAST_DATA_KWARGS)
    pce.data = data
    pce.save()


def get_telemetry_data(request, indent=None):
    """
    Get the telemetry data that would be sent.

    :param request: HTTP request. Optional.
    :type request: django.http.HttpRequest|None
    :return: Data blob.
    :rtype: str
    """
    data_dict = {
        "apps": settings.INSTALLED_APPS,
        "host": (request.get_host() if request else None),
        "key": get_installation_key(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "shoop_version": shoop.__version__,
    }
    return safe_json(data_dict, indent)


class TelemetryNotSent(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super(TelemetryNotSent, self).__init__(message, code)


def _send_telemetry(request, max_age_hours):
    if not is_telemetry_enabled():
        raise TelemetryNotSent("Telemetry not enabled", "disabled")

    if is_opt_out():
        raise TelemetryNotSent("Telemetry is opted-out", "optout")

    if is_in_grace_period():
        raise TelemetryNotSent("Telemetry in grace period", "grace")

    if max_age_hours is not None:
        last_send_time = get_last_submission_time()
        if last_send_time:
            if (now() - last_send_time).total_seconds() <= max_age_hours * 60 * 60:
                raise TelemetryNotSent("Trying to resend too soon", "age")

    data = get_telemetry_data(request)
    try:
        resp = requests.post(url=settings.SHOOP_TELEMETRY_URL, data=data, timeout=5)
    except Exception as exc:
        data = {
            "data": data,
            "error": force_text(exc),
        }
    else:
        data = {
            "data": data,
            "response": force_text(resp.content, errors="replace"),
            "status": resp.status_code,
        }
    save_telemetry_submission(data)
    return data


def try_send_telemetry(request=None, max_age_hours=72, raise_on_error=False):
    """
    Send telemetry information (unless opted-out, in grace period or disabled).

    :param request: HTTP request. Optional.
    :type request: django.http.HttpRequest|None
    :param max_age_hours: How many hours must have passed since the
                          last submission to be able to resend. If None,
                          not checked.

    :type max_age_hours: int|None
    :param raise_on_error: Raise exceptions when telemetry is not sent
                           instead of quietly returning False.
    :type raise_on_error: bool
    :return: Sent data (possibly with response information) or False if
             not sent.
    :rtype: dict|bool
    """
    try:
        return _send_telemetry(request=request, max_age_hours=max_age_hours)
    except TelemetryNotSent:
        if raise_on_error:
            raise
        return False
