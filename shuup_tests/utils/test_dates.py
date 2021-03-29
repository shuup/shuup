# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytz
from datetime import date, datetime, time

from shuup.utils.dates import parse_date, parse_datetime, to_aware, try_parse_date, try_parse_datetime, try_parse_time


def test_parse_date():
    now = datetime.now()
    today = date.today()

    date_fmt1 = "2016-12-31"
    date_fmt2 = "2016-12-31 15:40:34.404540"
    date_fmt3 = "12/31/2016"
    expected_date = date(2016, 12, 31)

    assert parse_date(now) == now.date()
    assert parse_date(today) == today
    assert parse_date(date_fmt1) == expected_date
    assert parse_date(date_fmt2) == expected_date
    assert parse_date(date_fmt3) == expected_date
    assert try_parse_date(1) is None


def test_parse_datetime():
    now = datetime.now()
    today = date.today()

    date_fmt1 = "2016-12-31"
    date_fmt2 = "2016-12-31 15:40:34.404540"
    date_fmt3 = "12/31/2016"

    assert parse_datetime(now) == now
    assert parse_datetime(today) == datetime.combine(today, datetime.min.time())
    assert parse_datetime(date_fmt1) == datetime(2016, 12, 31)
    assert parse_datetime(date_fmt2) == datetime(2016, 12, 31, 15, 40, 34, 404540)
    assert parse_datetime(date_fmt3) == datetime(2016, 12, 31)


def test_parse_time():
    now = datetime.now()

    time_fmt1 = "10:20"
    time_fmt2 = "12:32:21"

    assert try_parse_time(now) == now.time()
    assert try_parse_time(now.time()) == now.time()
    assert try_parse_time(time_fmt1) == time(10, 20)
    assert try_parse_time(time_fmt2) == time(12, 32, 21)
    assert try_parse_time("12341") is None


def test_try_parse_datetime():
    date_fmt1 = "2016-12-31 15:40:34"
    date_fmt2 = "2018-12-31 15:40"
    date_fmt3 = "12/31/2016"

    assert try_parse_datetime(date_fmt1) == datetime(2016, 12, 31, 15, 40, 34)
    assert try_parse_datetime(date_fmt2) == datetime(2018, 12, 31, 15, 40)
    assert try_parse_datetime(date_fmt3) == datetime(2016, 12, 31)
    assert try_parse_datetime("abc") is None


def test_dst_safe_aware():
    random_date = date(2018, 11, 4)

    sao_paulo = to_aware(random_date, tz=pytz.timezone("America/Sao_Paulo"))
    assert sao_paulo.hour == 0
    assert sao_paulo.minute == 0
    assert sao_paulo.tzinfo._dst.seconds == 3600  # 1hr

    madrid = to_aware(random_date, tz=pytz.timezone("Europe/Madrid"))
    assert madrid.hour == 0
    assert madrid.minute == 0
    assert madrid.tzinfo._dst.seconds == 0
