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
from django.core.exceptions import ValidationError
from django.template import engines
from django.test import override_settings
from django.utils import timezone
from mock import patch

from shuup.core.utils.price_cache import get_cached_price_info
from shuup.discounts.models import Discount, HappyHour, TimeRange
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.dates import to_timestamp
from shuup.utils.i18n import format_money


def init_test():
    shop = factories.get_default_shop()
    product = factories.create_product("test", shop=shop, default_price=10)
    discount = Discount.objects.create(active=True, product=product, discounted_price_value=6, shop=shop)
    happy_hour = HappyHour.objects.create(name="Happy", shop=shop)
    discount.happy_hours.add(happy_hour)
    return happy_hour


def set_valid_times_condition(happy_hour, hour_start, hour_end, matching_days):
    happy_hour.time_ranges.all().delete()
    for matching_day in matching_days.split(","):
        if hour_end < hour_start:
            with pytest.raises(ValidationError):  # Valid hours has to be splitted. Admin should take care of this.
                TimeRange.objects.create(
                    happy_hour=happy_hour, from_hour=hour_start, to_hour=hour_end, weekday=matching_day
                )

            matching_day = int(matching_day)
            tomorrow = matching_day + 1 if matching_day < 6 else 0
            parent = TimeRange.objects.create(
                happy_hour=happy_hour,
                from_hour=hour_start,
                to_hour=datetime.time(hour=23, minute=59),
                weekday=matching_day,
            )
            TimeRange.objects.create(
                happy_hour=happy_hour,
                parent=parent,
                from_hour=datetime.time(hour=0),
                to_hour=hour_end,
                weekday=tomorrow,
            )
        else:
            TimeRange.objects.create(
                happy_hour=happy_hour, from_hour=hour_start, to_hour=hour_end, weekday=matching_day
            )


def mocked_now_basic():
    # Hour 10 weekday monday (0). At the same time in the LA it is already monday and time is 2:00 AM.
    return datetime.datetime(2017, 12, 4, 10, 0, tzinfo=pytz.UTC)


@patch("django.utils.timezone.now", side_effect=mocked_now_basic)
@pytest.mark.django_db
def test_happy_hour(rf):
    happy_hour = init_test()

    discount = happy_hour.discounts.first()
    shop = discount.shop
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
        # Timezone needs to be activated to current one because some old timezone can still be active
        timezone.activate(pytz.timezone("America/Los_Angeles"))

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
    timezone.activate(pytz.UTC)
    happy_hour = init_test()

    shop = happy_hour.shop
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
    timezone.activate(pytz.UTC)
    happy_hour = init_test()
    shop = happy_hour.shop

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
        # Timezone needs to be activated to current one because some old timezone can still be active
        timezone.activate(pytz.timezone("America/Los_Angeles"))

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
    timezone.activate(pytz.UTC)
    happy_hour = init_test()
    shop = happy_hour.shop

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


@pytest.mark.django_db
def test_happy_hour_prices_expiration(rf):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_happy_hour_prices_bump",
            }
        }
    ):
        happy_hour = init_test()

        # it is now: 2018-01-01 09:00 AM
        before_happy_hour = datetime.datetime(2018, 1, 1, 9, 0, tzinfo=pytz.UTC)  # 09:00 AM
        inside_happy_hour = datetime.datetime(2018, 1, 1, 10, 30, tzinfo=pytz.UTC)  # 10:30 AM
        after_happy_hours = datetime.datetime(2018, 1, 1, 11, 20, tzinfo=pytz.UTC)  # 11:30 AM

        # Create condition from 10am to 11am
        hour_start = datetime.datetime(2018, 1, 1, 10, 0, tzinfo=pytz.UTC).time()  # 10:00 AM
        hour_end = datetime.datetime(2018, 1, 1, 11, 0, tzinfo=pytz.UTC).time()  # 11:00 AM
        set_valid_times_condition(happy_hour, hour_start, hour_end, str(before_happy_hour.weekday()))

        shop = happy_hour.shop
        discount = happy_hour.discounts.first()
        product = discount.product
        shop_product = product.get_shop_instance(shop)
        assert shop_product.default_price_value == 10
        assert discount.discounted_price_value == 6

        def get_request():
            return apply_request_middleware(rf.get("/"))

        price_template = engines["jinja2"].from_string("{{ product|price }}")
        is_discounted_template = engines["jinja2"].from_string("{{ product|is_discounted }}")
        discount_percent_template = engines["jinja2"].from_string("{{ product|discount_percent }}")

        # we start with time being before happy hour
        with patch("django.utils.timezone.now", new=lambda: before_happy_hour):
            # mock also time.time so the cache timeout will be calculated correctly
            with patch("time.time", new=lambda: to_timestamp(before_happy_hour)):
                # check that product price is still the orignal (€10.00)
                # run twice to make sure caches are being used
                for cache_test in range(2):
                    context = dict(product=product, request=get_request())
                    assert price_template.render(context) == format_money(shop_product.default_price)
                    assert is_discounted_template.render(context) == "False"
                    assert discount_percent_template.render(context) == "0%"

                    if cache_test == 1:
                        assert get_cached_price_info(get_request(), product, 1, supplier=shop_product.get_supplier())

        # now we are inside happy hour range
        with patch("django.utils.timezone.now", new=lambda: inside_happy_hour):
            # mock also time.time so the cache timeout will be calculated correctly
            with patch("time.time", new=lambda: to_timestamp(inside_happy_hour)):
                # check that product price is the discounted one (€6.00)
                # run twice to make sure caches are being used
                for cache_test in range(2):
                    context = dict(product=product, request=get_request())
                    assert price_template.render(context) == format_money(
                        shop.create_price(discount.discounted_price_value)
                    )
                    assert is_discounted_template.render(context) == "True"
                    assert discount_percent_template.render(context) == "40%"

                    if cache_test == 1:
                        assert get_cached_price_info(get_request(), product, 1, supplier=shop_product.get_supplier())

                # we change the discounted price from $6 to $7
                # cached should be bumped
                discount.discounted_price_value = 7
                discount.save()
                for cache_test in range(2):
                    context = dict(product=product, request=get_request())
                    assert price_template.render(context) == format_money(
                        shop.create_price(discount.discounted_price_value)
                    )
                    assert is_discounted_template.render(context) == "True"
                    assert discount_percent_template.render(context) == "30%"

                    if cache_test == 1:
                        assert get_cached_price_info(get_request(), product, 1, supplier=shop_product.get_supplier())

        # now we are inside happy hour range
        with patch("django.utils.timezone.now", new=lambda: after_happy_hours):
            # mock also time.time so the cache timeout will be calculated correctly
            with patch("time.time", new=lambda: to_timestamp(after_happy_hours)):
                # check that product price is the orignal (€10.00)
                # run twice to make sure caches are being used
                for cache_test in range(2):
                    context = dict(product=product, request=get_request())
                    assert price_template.render(context) == format_money(shop_product.default_price)
                    assert is_discounted_template.render(context) == "False"
                    assert discount_percent_template.render(context) == "0%"

                    if cache_test == 1:
                        assert get_cached_price_info(get_request(), product, 1, supplier=shop_product.get_supplier())
