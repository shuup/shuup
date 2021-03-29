# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import platform
import requests
import sys
from datetime import date, datetime, time, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Sum
from django.utils.crypto import get_random_string
from django.utils.timezone import now

import shuup
from shuup import configuration
from shuup.core.models import Contact, Order, Payment, PersistentCacheEntry, Product
from shuup.utils.django_compat import force_text

User = get_user_model()

OPT_OUT_KWARGS = dict(module="telemetry", key="opt_out")
INSTALLATION_KEY_KWARGS = dict(module="telemetry", key="installation_key")
LAST_DATA_KWARGS = dict(module="telemetry", key="last_data")


def safe_json(data_dict, indent=None):
    return json.dumps(data_dict, cls=DjangoJSONEncoder, sort_keys=True, indent=indent)


def get_installation_key():
    """
    Get the unique installation ID for this Shuup instance.

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
    return (now() - installation_time).total_seconds() < 60 * 60 * 24


def is_telemetry_enabled():
    return bool(settings.SHUUP_TELEMETRY_ENABLED)


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


def daterange(start_date, end_date):
    if start_date == end_date:
        yield start_date

    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def get_daily_data_for_day(date):
    data = {"date": date.strftime("%Y-%m-%d")}
    data["methods"] = {}

    today_min = datetime.combine(date, time.min)
    today_max = datetime.combine(date, time.max)
    order_date_filter = Q(order_date__range=(today_min, today_max))
    data["orders"] = Order.objects.filter(order_date_filter).count()
    total_sales = Order.objects.filter(order_date_filter).aggregate(total_sales=Sum("taxful_total_price_value"))
    data["total_sales"] = float(total_sales["total_sales"]) if total_sales["total_sales"] else 0

    created_on_filter = Q(created_on__range=(today_min, today_max))
    total_paid_sales = Payment.objects.filter(created_on_filter).aggregate(total_paid=Sum("amount_value"))
    data["total_paid_sales"] = float(total_paid_sales["total_paid"]) if total_paid_sales["total_paid"] else 0
    for service_identifier in ["stripe", "checkoutfi", "paytrail"]:
        payment_query = created_on_filter & Q(order__payment_method__choice_identifier=service_identifier)
        total_sales = Payment.objects.filter(payment_query).aggregate(total_sales=Sum("amount_value"))
        data["methods"][service_identifier] = float(total_sales["total_sales"]) if total_sales["total_sales"] else 0

    data["products"] = Product.objects.filter(created_on_filter).count()
    data["contacts"] = Contact.objects.filter(created_on_filter).count()

    return data


def get_daily_data(today):
    last_time = get_last_submission_time()
    if not last_time:
        return []

    data = []
    data_start_date = date(last_time.year, last_time.month, last_time.day)
    data_end_date = date(today.year, today.month, today.day) - timedelta(days=1)
    for i, day in enumerate(daterange(data_start_date, data_end_date)):
        if i > settings.SHUUP_MAX_DAYS_IN_TELEMETRY:
            break
        data.append(get_daily_data_for_day(day))
    return data


def get_telemetry_data(request, indent=None):
    """
    Get the telemetry data that would be sent.

    :param request: HTTP request. Optional.
    :type request: django.http.HttpRequest|None
    :return: Data blob.
    :rtype: str
    """
    admin_user = User.objects.first()
    data_dict = {
        "daily_data": get_daily_data(now()),
        "apps": settings.INSTALLED_APPS,
        "debug": settings.DEBUG,
        "host": (request.get_host() if request else None),
        "key": get_installation_key(),
        "machine": platform.machine(),
        "admin_user": admin_user.email if admin_user else None,
        "last_login": admin_user.last_login if admin_user else None,
        "platform": platform.platform(),
        "python_version": sys.version,
        "shuup_version": shuup.__version__,
    }
    return safe_json(data_dict, indent)


class TelemetryNotSent(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super(TelemetryNotSent, self).__init__(message, code)


def _send_telemetry(request, max_age_hours, force_send=False):
    if not is_telemetry_enabled():
        raise TelemetryNotSent("Error! Telemetry not enabled.", "disabled")

    if not force_send:
        if is_opt_out():
            raise TelemetryNotSent("Error! Telemetry is opted-out.", "optout")

        if is_in_grace_period():
            raise TelemetryNotSent("Error! Telemetry in grace period.", "grace")

    if max_age_hours is not None:
        last_send_time = get_last_submission_time()
        if last_send_time and (now() - last_send_time).total_seconds() <= max_age_hours * 60 * 60:
            raise TelemetryNotSent("Trying to resend too soon", "age")

    data = get_telemetry_data(request)
    try:
        resp = requests.post(url=settings.SHUUP_TELEMETRY_URL, data=data, timeout=5)
        if (
            not settings.DEBUG
            and resp.status_code == 200
            and resp.json().get("support_id")
            and not configuration.get(None, "shuup_support_id")
        ):
            configuration.set(None, "shuup_support_id", resp.json().get("support_id"))
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


def try_send_telemetry(request=None, max_age_hours=24, raise_on_error=False):
    """
    Send telemetry information (unless opted-out, in grace period or disabled).

    Telemetry will be always sent if there is no prior sending information.

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
    force_send = bool(not get_last_submission_time() or not settings.DEBUG)
    try:
        return _send_telemetry(request=request, max_age_hours=max_age_hours, force_send=force_send)
    except TelemetryNotSent:
        if raise_on_error:
            raise
        return False
