# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

import pytest
import pytz
from mock import patch

from shuup.discounts.models import AvailabilityException, Discount
from shuup.testing import factories


@pytest.mark.django_db
def test_availability_simple():
    shop = factories.get_default_shop()

    # Just active discount without date ranges
    Discount.objects.create(active=False)
    assert Discount.objects.available().count() == 0
    Discount.objects.update(active=True)
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 0

    # Add shop and availability with shop should return the one and
    # only discount
    product_discount = Discount.objects.available().first()
    product_discount.shops.add(shop)
    assert Discount.objects.available(shop).count() == 1

    # Test simple date ranges
    discount_start = datetime.datetime(2017, 12, 5, 7, 0, tzinfo=pytz.UTC)
    Discount.objects.update(start_datetime=discount_start)

    # Discount not started yet
    def invalid_date():
        return datetime.datetime(2017, 12, 5, 6, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=invalid_date):
        assert Discount.objects.available(shop).count() == 0

    # Discount just started
    def valid_date():
        return datetime.datetime(2017, 12, 5, 7, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=valid_date):
        assert Discount.objects.available(shop).count() == 1

    # Let's go fast forward few days
    def valid_future():
        return datetime.datetime(2017, 12, 15, 7, 0, tzinfo=pytz.UTC)

    # Still available
    with patch("django.utils.timezone.now", side_effect=valid_future):
        assert Discount.objects.available(shop).count() == 1

    # Let's set end date for discount
    discount_end = datetime.datetime(2017, 12, 15, 7, 0, tzinfo=pytz.UTC)
    Discount.objects.update(end_datetime=discount_end)

    # Last minute for this discount
    with patch("django.utils.timezone.now", side_effect=valid_future):
        assert Discount.objects.available(shop).count() == 1

    def invalid_future():
        return datetime.datetime(2017, 12, 15, 7, 1, tzinfo=pytz.UTC)

    # Discount should be now ended
    with patch("django.utils.timezone.now", side_effect=invalid_future):
        assert Discount.objects.available(shop).count() == 0

    # Exclude some time range inside discount date range
    exclude_start = datetime.datetime(2017, 12, 10, 7, 0, tzinfo=pytz.UTC)
    exclude_end = datetime.datetime(2017, 12, 10, 12, 0, tzinfo=pytz.UTC)

    exception = AvailabilityException.objects.create(
        name="Anti-Midsummer", start_datetime=exclude_start, end_datetime=exclude_end)
    exception.discounts.add(Discount.objects.first())

    def valid_just_before_exclude():
        return datetime.datetime(2017, 12, 10, 6, 59, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=valid_just_before_exclude):
        assert Discount.objects.available(shop).count() == 1

    def valid_just_after_exclude():
        return datetime.datetime(2017, 12, 10, 12, 1, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=valid_just_after_exclude):
        assert Discount.objects.available(shop).count() == 1

    def invalid_exclude_just_started():
        return datetime.datetime(2017, 12, 10, 7, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=invalid_exclude_just_started):
        assert Discount.objects.available(shop).count() == 0

    def invalid_between_excluded_range():
        return datetime.datetime(2017, 12, 10, 10, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=invalid_between_excluded_range):
        assert Discount.objects.available(shop).count() == 0

    def invalid_last_minute_of_excluded_range():
        return datetime.datetime(2017, 12, 10, 12, 0, tzinfo=pytz.UTC)

    with patch("django.utils.timezone.now", side_effect=invalid_last_minute_of_excluded_range):
        assert Discount.objects.available(shop).count() == 0


@pytest.mark.django_db
def test_with_multiple_exceptions():
    shop = factories.get_default_shop()

    # Just active discount without date ranges
    Discount.objects.create(active=False)
    assert Discount.objects.available().count() == 0
    Discount.objects.update(active=True)
    assert Discount.objects.available().count() == 1
    assert Discount.objects.available(shop).count() == 0

    # Add shop and availability with shop should return the one and
    # only discount
    product_discount = Discount.objects.available().first()
    product_discount.shops.add(shop)
    assert Discount.objects.available(shop).count() == 1

    for day in [10, 13, 21]:
        exclude_start = datetime.datetime(2017, 12, day, 7, 0, tzinfo=pytz.UTC)
        exclude_end = datetime.datetime(2017, 12, day, 12, 0, tzinfo=pytz.UTC)

        exception = AvailabilityException.objects.create(
            name="Disable basic discounts for december",
            start_datetime=exclude_start,
            end_datetime=exclude_end
        )
        exception.discounts.add(Discount.objects.first())

        def valid_just_before_exclude():
            return datetime.datetime(2017, 12, day, 6, 59, tzinfo=pytz.UTC)

        with patch("django.utils.timezone.now", side_effect=valid_just_before_exclude):
            assert Discount.objects.available(shop).count() == 1

        def valid_just_after_exclude():
            return datetime.datetime(2017, 12, day, 12, 1, tzinfo=pytz.UTC)

        with patch("django.utils.timezone.now", side_effect=valid_just_after_exclude):
            assert Discount.objects.available(shop).count() == 1

        def invalid_exclude_just_started():
            return datetime.datetime(2017, 12, day, 7, 0, tzinfo=pytz.UTC)

        with patch("django.utils.timezone.now", side_effect=invalid_exclude_just_started):
            assert Discount.objects.available(shop).count() == 0

        def invalid_between_excluded_range():
            return datetime.datetime(2017, 12, day, 10, 0, tzinfo=pytz.UTC)

        with patch("django.utils.timezone.now", side_effect=invalid_between_excluded_range):
            assert Discount.objects.available(shop).count() == 0

        def invalid_last_minute_of_excluded_range():
            return datetime.datetime(2017, 12, day, 12, 0, tzinfo=pytz.UTC)

        with patch("django.utils.timezone.now", side_effect=invalid_last_minute_of_excluded_range):
            assert Discount.objects.available(shop).count() == 0

        # Disabling discount should work
        Discount.objects.update(active=False)
        with patch("django.utils.timezone.now", side_effect=valid_just_before_exclude):
            assert Discount.objects.available(shop).count() == 0

        with patch("django.utils.timezone.now", side_effect=valid_just_after_exclude):
            assert Discount.objects.available(shop).count() == 0

        Discount.objects.update(active=True)
