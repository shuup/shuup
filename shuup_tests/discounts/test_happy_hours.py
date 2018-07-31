# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

import pytest
import pytz
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone
from mock import patch

from shuup.discounts.models import Discount, HappyHour, TimeRange
from shuup.testing import factories


def init_test():
    shop = factories.get_default_shop()
    product = factories.create_product("test", shop=shop, default_price=10)
    discount = Discount.objects.create(active=True, product=product, discounted_price_value=6)
    discount.shops = [shop]
    happy_hour = HappyHour.objects.create(name="Happy")
    happy_hour.shops = [shop]
    discount.happy_hours = [happy_hour]
    return happy_hour


def set_valid_times_condition(happy_hour, hour_start, hour_end, matching_days):
    happy_hour.time_ranges.all().delete()
    for matching_day in matching_days.split(","):
        if hour_end < hour_start:
            with pytest.raises(ValidationError):  # Valid hours has to be splitted. Admin should take care of this.
                TimeRange.objects.create(
                    happy_hour=happy_hour, from_hour=hour_start, to_hour=hour_end, weekday=matching_day)

            matching_day = int(matching_day)
            tomorrow = (matching_day + 1 if matching_day < 6 else 0)
            parent = TimeRange.objects.create(
                happy_hour=happy_hour, from_hour=hour_start, to_hour=datetime.time(hour=23), weekday=matching_day)
            TimeRange.objects.create(
                happy_hour=happy_hour, parent=parent, from_hour=datetime.time(hour=0),
                to_hour=hour_end, weekday=tomorrow)
        else:
            TimeRange.objects.create(
                happy_hour=happy_hour, from_hour=hour_start, to_hour=hour_end, weekday=matching_day)


def mocked_now_basic():
    # Hour 10 weekday monday (0). At the same time in the LA it is already monday and time is 2:00 AM.
    return datetime.datetime(2017, 12, 4, 10, 0, tzinfo=pytz.UTC)


@patch("django.utils.timezone.now", side_effect=mocked_now_basic)
@pytest.mark.django_db
def test_happy_hour(rf):
    happy_hour = init_test()

    discount = happy_hour.discounts.first()
    shop = discount.shops.first()
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 1

    w_today = timezone.now().date().weekday()
    w_tomorrow = (timezone.now() + datetime.timedelta(days=1)).date().weekday()
    w_future = (timezone.now() + datetime.timedelta(days=2)).date().weekday()
    matching_days = ",".join(map(str, [w_today]))
    non_matching_days = ",".join(map(str, [w_tomorrow, w_future]))

    # Matching time range
    hour_start = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    hour_end = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 PM
    set_valid_times_condition(happy_hour, hour_start, hour_end, matching_days)
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 1

    set_valid_times_condition(happy_hour, hour_start, hour_end, non_matching_days)
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0

    # Hour end shouldn't cause a match. Should be obvious that if the
    # merchant set start time 8:00 AM and end time 10:00 AM th campaign is no more
    # at 10:10 AM
    new_hour_start = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    new_hour_end = timezone.now().time()  # 10:00 PM
    set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, non_matching_days)
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0

    # time in future shouldn't match
    new_hour_start = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 PM
    new_hour_end = (timezone.now() + datetime.timedelta(hours=4)).time()  # 14:00 PM
    set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0

    # time in past shouldn't match
    new_hour_start = (timezone.now() - datetime.timedelta(hours=3)).time()  # 7:00 AM
    new_hour_end = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0

    # Special times (should match)
    new_hour_start = timezone.now().time()  # 10:00 AM
    new_hour_end = (timezone.now() + datetime.timedelta(hours=14)).time()  # 0:00 AM
    set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 1

    set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, non_matching_days)
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0

    # Special times (should not match)
    new_hour_start = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 AM
    new_hour_end = (timezone.now() + datetime.timedelta(hours=14)).time()  # 0:00 AM
    set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0

    # Lastly few timezone tests (LA it is monday and time is 2:00 AM.)
    with override_settings(TIME_ZONE="America/Los_Angeles"):
        # So the 10:00 AM shouldn't match at all
        new_hour_start = (timezone.now() - datetime.timedelta(hours=1)).time()  # 9:00 AM
        new_hour_end = (timezone.now() + datetime.timedelta(hours=1)).time()  # 11:00 AM
        set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
        assert Discount.objects.available().count() == 0
        assert Discount.objects.available(shop).count() == 0

        # Instead around 2:00 AM we will find a match
        new_hour_start = (timezone.now() - datetime.timedelta(hours=9)).time()  # 1:00 AM
        new_hour_end = (timezone.now() - datetime.timedelta(hours=7)).time()  # 3:00 AM
        set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
        assert Discount.objects.available().count() == 1
        assert Discount.objects.available(shop).count() == 1

        # Make sure that the hour end doesn't cause match
        new_hour_start = (timezone.now() - datetime.timedelta(hours=9)).time()  # 1:00 AM
        new_hour_end = (timezone.now() - datetime.timedelta(hours=8)).time()  # 2:00 AM
        set_valid_times_condition(happy_hour, new_hour_start, new_hour_end, matching_days)
        assert Discount.objects.available().count() == 0
        assert Discount.objects.available(shop).count() == 0


@patch("django.utils.timezone.now", side_effect=mocked_now_basic)
@pytest.mark.django_db
def test_time_ranges_are_still_honored(rf):
    happy_hour = init_test()

    shop = happy_hour.shops.first()
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 1

    w_today = timezone.now().date().weekday()
    matching_days = ",".join(map(str, [w_today]))

    # Matching time range
    hour_start = (timezone.now() - datetime.timedelta(hours=2)).time()  # 8:00 AM
    hour_end = (timezone.now() + datetime.timedelta(hours=2)).time()  # 12:00 PM
    set_valid_times_condition(happy_hour, hour_start, hour_end, matching_days)
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 1

    # Let's make the discount 2018 only and it shouldn't match anymore
    discount = happy_hour.discounts.first()
    discount.start_datetime = datetime.datetime(2018, 1, 1, 0, 0, tzinfo=pytz.UTC)
    discount.save()
    assert Discount.objects.available().count() == 0
    assert Discount.objects.available(shop).count() == 0


def mocked_now_weekday_change():
    # Hour 3 weekday monday (0). At the same time in the LA it is still sunday and time is 7:00 PM.
    return datetime.datetime(2017, 12, 4, 3, 0, tzinfo=pytz.UTC)


@patch("django.utils.timezone.now", side_effect=mocked_now_weekday_change)
@pytest.mark.django_db
def test_happy_hour_localized_weekday(rf):
    happy_hour = init_test()
    shop = happy_hour.shops.first()

    w_today = timezone.now().date().weekday()
    w_yesterday = (timezone.now() - datetime.timedelta(days=1)).date().weekday()
    matching_day_for_utc = ",".join(map(str, [w_today]))
    matching_day_for_la = ",".join(map(str, [w_yesterday]))

    # Matching time range
    hour_start = (timezone.now().replace(hour=1)).time()  # 1:00 AM
    hour_end = (timezone.now().replace(hour=4)).time()  # 4:00 PM
    set_valid_times_condition(happy_hour, hour_start, hour_end, matching_day_for_utc)
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 1

    # Lastly few timezone tests (LA it is monday and time is 2:00 AM.)
    with override_settings(TIME_ZONE="America/Los_Angeles"):
        # Matching to UTC date doesn't work
        hour_start = (timezone.now().replace(hour=17)).time()  # 5:00 PM
        hour_end = (timezone.now().replace(hour=20)).time()  # 8:00 PM
        set_valid_times_condition(happy_hour, hour_start, hour_end, matching_day_for_utc)
        assert Discount.objects.available().count() == 0
        assert Discount.objects.available(shop).count() == 0

        # Update weekday to LA matching and we should get match
        set_valid_times_condition(happy_hour, hour_start, hour_end, matching_day_for_la)
        assert Discount.objects.available().count() == 1
        assert Discount.objects.available(shop).count() == 1


@pytest.mark.django_db
def test_hour_conditions_end_before_start():
    happy_hour = init_test()
    shop = happy_hour.shops.first()

    # Create condition from 5pm to 1am for monday
    hour_start = (timezone.now().replace(hour=17, minute=0)).time()  # 5:00 PM
    hour_end = (timezone.now().replace(hour=1, minute=0)).time()  # 1:00 AM
    set_valid_times_condition(happy_hour, hour_start, hour_end, "0")

    def valid_date_1():
        return datetime.datetime(2017, 12, 4, 17, 1, tzinfo=pytz.UTC)

    def valid_date_2():
        return datetime.datetime(2017, 12, 4, 18, 0, tzinfo=pytz.UTC)

    def valid_date_3():
        return datetime.datetime(2017, 12, 5, 0, 0, tzinfo=pytz.UTC)

    def valid_date_4():
        return datetime.datetime(2017, 12, 5, 0, 59, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=valid_date_1):
        assert Discount.objects.available().count() == 1
        assert Discount.objects.available(shop).count() == 1

    with patch("django.utils.timezone.now", side_effect=valid_date_2):
        assert Discount.objects.available().count() == 1
        assert Discount.objects.available(shop).count() == 1

    with patch("django.utils.timezone.now", side_effect=valid_date_3):
        assert Discount.objects.available().count() == 1
        assert Discount.objects.available(shop).count() == 1

    with patch("django.utils.timezone.now", side_effect=valid_date_4):
        assert Discount.objects.available().count() == 1
        assert Discount.objects.available(shop).count() == 1

    def invalid_date_1():
        return datetime.datetime(2017, 12, 4, 16, 59, tzinfo=pytz.UTC)

    def invalid_date_2():
        return datetime.datetime(2017, 12, 5, 1, 1, tzinfo=pytz.UTC)

    def invalid_date_3():
        return datetime.datetime(2017, 12, 5, 18, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=invalid_date_1):
        assert Discount.objects.available().count() == 0
        assert Discount.objects.available(shop).count() == 0

    with patch("django.utils.timezone.now", side_effect=invalid_date_2):
        assert Discount.objects.available().count() == 0
        assert Discount.objects.available(shop).count() == 0

    with patch("django.utils.timezone.now", side_effect=invalid_date_3):
        assert Discount.objects.available().count() == 0
        assert Discount.objects.available(shop).count() == 0
