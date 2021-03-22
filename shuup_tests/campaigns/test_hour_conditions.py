# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import pytest
import pytz
from django.test import override_settings
from django.utils import timezone
from mock import patch

from shuup.campaigns.models.basket_conditions import HourBasketCondition
from shuup.campaigns.models.context_conditions import HourCondition


def get_basket_condition(hour_start, hour_end, matching_days):
    return HourBasketCondition.objects.create(hour_start=hour_start, hour_end=hour_end, days=matching_days)


def get_context_condition(hour_start, hour_end, matching_days):
    return HourCondition.objects.create(hour_start=hour_start, hour_end=hour_end, days=matching_days)


def mocked_now_basic():
    # Hour 10 weekday monday (0). At the same time in the LA it is already monday and time is 2:00 AM.
    return datetime.datetime(2017, 12, 4, 10, 0, tzinfo=pytz.UTC)


@patch("django.utils.timezone.now", side_effect=mocked_now_basic)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_condition,params_for_matches", {(get_basket_condition, (None, None)), (get_context_condition, (None,))}
)
def test_hour_conditions(rf, get_condition, params_for_matches):
    timezone.activate(pytz.UTC)
    w_today = timezone.now().date().weekday()
    w_tomorrow = (timezone.now() + datetime.timedelta(days=1)).date().weekday()
    w_future = (timezone.now() + datetime.timedelta(days=2)).date().weekday()
    matching_days = ",".join(map(str, [w_today]))
    non_matching_days = ",".join(map(str, [w_tomorrow, w_future]))

    # Matching time range
    hour_start = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    hour_end = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 PM
    hour_condition = get_condition(hour_start, hour_end, matching_days)
    assert hour_condition.matches(*params_for_matches)

    hour_condition.days = non_matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    # Hour end shouldn't cause a match. Should be obvious that if the
    # merchant set start time 8:00 AM and end time 10:00 AM th campaign is no more
    # at 10:10 AM
    hour_condition.hour_start = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    hour_condition.hour_end = timezone.now().time()  # 10:00 PM
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    # time in future shouldn't match
    hour_condition.hour_start = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 PM
    hour_condition.hour_end = (timezone.now() + datetime.timedelta(hours=4)).time()  # 14:00 PM

    hour_condition.days = matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    hour_condition.days = non_matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    # time in past shouldn't match
    hour_condition.hour_start = (timezone.now() - datetime.timedelta(hours=3)).time()  # 7:00 AM
    hour_condition.hour_end = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    hour_condition.days = matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    hour_condition.days = non_matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    # Special times (should match)
    hour_condition.hour_start = timezone.now().time()  # 10:00 AM
    hour_condition.hour_end = (timezone.now() + datetime.timedelta(hours=14)).time()  # 0:00 AM
    hour_condition.days = matching_days
    hour_condition.save()
    assert hour_condition.matches(*params_for_matches)

    hour_condition.days = non_matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    # Special times (should not match)
    hour_condition.hour_start = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 AM
    hour_condition.hour_end = (timezone.now() + datetime.timedelta(hours=14)).time()  # 0:00 AM
    hour_condition.days = matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    hour_condition.days = non_matching_days
    hour_condition.save()
    assert not hour_condition.matches(*params_for_matches)

    # Lastly few timezone tests (LA it is monday and time is 2:00 AM.)
    with override_settings(TIME_ZONE="America/Los_Angeles"):
        timezone.activate(pytz.timezone("America/Los_Angeles"))
        # So the 10:00 AM shouldn't match at all
        hour_condition.hour_start = (timezone.now() - datetime.timedelta(hours=1)).time()  # 9:00 AM
        hour_condition.hour_end = (timezone.now() + datetime.timedelta(hours=1)).time()  # 11:00 AM
        hour_condition.days = matching_days
        hour_condition.save()
        assert not hour_condition.matches(*params_for_matches)

        # Instead around 2:00 AM we will find a match
        hour_condition.hour_start = (timezone.now() - datetime.timedelta(hours=9)).time()  # 1:00 AM
        hour_condition.hour_end = (timezone.now() - datetime.timedelta(hours=7)).time()  # 3:00 AM
        hour_condition.days = matching_days
        hour_condition.save()
        assert hour_condition.matches(*params_for_matches)

        # Make sure that the hour end doesn't cause match
        hour_condition.hour_start = (timezone.now() - datetime.timedelta(hours=9)).time()  # 1:00 AM
        hour_condition.hour_end = (timezone.now() - datetime.timedelta(hours=8)).time()  # 2:00 AM
        hour_condition.days = matching_days
        hour_condition.save()
        assert not hour_condition.matches(*params_for_matches)


def mocked_now_weekday_change():
    # Hour 3 weekday monday (0). At the same time in the LA it is still sunday and time is 7:00 PM.
    return datetime.datetime(2017, 12, 4, 3, 0, tzinfo=pytz.UTC)


@patch("django.utils.timezone.now", side_effect=mocked_now_weekday_change)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_condition,params_for_matches", {(get_basket_condition, (None, None)), (get_context_condition, (None,))}
)
def test_hour_conditions_localized_weekday(rf, get_condition, params_for_matches):
    timezone.activate(pytz.UTC)
    w_today = timezone.now().date().weekday()
    w_yesterday = (timezone.now() - datetime.timedelta(days=1)).date().weekday()
    matching_day_for_utc = ",".join(map(str, [w_today]))
    matching_day_for_la = ",".join(map(str, [w_yesterday]))

    # Matching time range
    hour_start = (timezone.now().replace(hour=1)).time()  # 1:00 AM
    hour_end = (timezone.now().replace(hour=4)).time()  # 4:00 PM
    hour_condition = get_condition(hour_start, hour_end, matching_day_for_utc)
    assert hour_condition.matches(*params_for_matches)

    # Lastly few timezone tests (LA it is monday and time is 2:00 AM.)
    with override_settings(TIME_ZONE="America/Los_Angeles"):
        timezone.activate(pytz.timezone("America/Los_Angeles"))
        # Matching to UTC date doesn't work
        hour_start = (timezone.now().replace(hour=17)).time()  # 5:00 PM
        hour_end = (timezone.now().replace(hour=20)).time()  # 8:00 PM
        hour_condition = get_condition(hour_start, hour_end, matching_day_for_utc)
        assert not hour_condition.matches(*params_for_matches)

        # Update weekday to LA matching and we should get match
        hour_condition.days = matching_day_for_la
        hour_condition.save()
        assert hour_condition.matches(*params_for_matches)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_condition,params_for_matches", {(get_basket_condition, (None, None)), (get_context_condition, (None,))}
)
def test_hour_conditions_end_before_start(rf, get_condition, params_for_matches):
    timezone.activate(pytz.UTC)
    # Create condition from 5pm to 1am for monday
    hour_start = (timezone.now().replace(hour=17, minute=0)).time()  # 5:00 PM
    hour_end = (timezone.now().replace(hour=1, minute=0)).time()  # 1:00 AM
    hour_condition = get_condition(hour_start, hour_end, "0")

    def valid_date_1():
        return datetime.datetime(2017, 12, 4, 17, 1, tzinfo=pytz.UTC)

    def valid_date_2():
        return datetime.datetime(2017, 12, 4, 18, 0, tzinfo=pytz.UTC)

    def valid_date_3():
        return datetime.datetime(2017, 12, 5, 0, 0, tzinfo=pytz.UTC)

    def valid_date_4():
        return datetime.datetime(2017, 12, 5, 0, 59, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=valid_date_1):
        assert hour_condition.matches(*params_for_matches)

    with patch("django.utils.timezone.now", side_effect=valid_date_2):
        assert hour_condition.matches(*params_for_matches)

    with patch("django.utils.timezone.now", side_effect=valid_date_3):
        assert hour_condition.matches(*params_for_matches)

    with patch("django.utils.timezone.now", side_effect=valid_date_4):
        assert hour_condition.matches(*params_for_matches)

    def invalid_date_1():
        return datetime.datetime(2017, 12, 4, 16, 59, tzinfo=pytz.UTC)

    def invalid_date_2():
        return datetime.datetime(2017, 12, 5, 1, 1, tzinfo=pytz.UTC)

    def invalid_date_3():
        return datetime.datetime(2017, 12, 5, 18, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=invalid_date_1):
        assert not hour_condition.matches(*params_for_matches)

    with patch("django.utils.timezone.now", side_effect=invalid_date_2):
        assert not hour_condition.matches(*params_for_matches)

    with patch("django.utils.timezone.now", side_effect=invalid_date_3):
        assert not hour_condition.matches(*params_for_matches)
