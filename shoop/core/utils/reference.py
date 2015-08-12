# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.utils.encoding import force_text
from shoop.core.models.counters import Counter, CounterType
from shoop.utils.importing import load
import datetime


def calc_reference_number_checksum(rn):
    muls = (7, 3, 1)
    s = 0
    for i, ch in enumerate(rn[::-1]):
        s += muls[i % 3] * int(ch)
    s = 10 - (s % 10)
    return force_text(s)[-1]


def get_unique_reference_number(order):
    now = datetime.datetime.now()
    dt = "%012s%07d%04d" % (now.strftime("%y%m%d%H%M%S"), now.microsecond * 1000000, order.pk % 1000)
    return dt + calc_reference_number_checksum(dt)


def get_running_reference_number(order):
    value = Counter.get_and_increment(CounterType.ORDER_REFERENCE)
    prefix = settings.SHOOP_REFERENCE_NUMBER_PREFIX
    padded_value = force_text(value).rjust(settings.SHOOP_REFERENCE_NUMBER_LENGTH - len(prefix), "0")
    reference_no = "%s%s" % (prefix, padded_value)
    return reference_no + calc_reference_number_checksum(reference_no)


def get_shop_running_reference_number(order):
    value = Counter.get_and_increment(CounterType.ORDER_REFERENCE)
    prefix = "%06d" % order.shop.pk
    padded_value = force_text(value).rjust(settings.SHOOP_REFERENCE_NUMBER_LENGTH - len(prefix), "0")
    reference_no = "%s%s" % (prefix, padded_value)
    return reference_no + calc_reference_number_checksum(reference_no)


def get_reference_number(order):
    if order.reference_number:
        raise ValueError("Order passed to get_reference_number() already has a reference number")
    reference_number_method = settings.SHOOP_REFERENCE_NUMBER_METHOD
    if reference_number_method == "unique":
        return get_unique_reference_number(order)
    elif reference_number_method == "running":
        return get_running_reference_number(order)
    elif reference_number_method == "shop_running":
        return get_shop_running_reference_number(order)
    elif callable(reference_number_method):
        return reference_number_method(order)
    else:
        getter = load(reference_number_method, "Reference number generator")
        return getter(order)


def get_order_identifier(order):
    if order.identifier:
        raise ValueError("Order passed to get_order_identifier() already has an identifier")
    order_identifier_method = settings.SHOOP_ORDER_IDENTIFIER_METHOD
    if order_identifier_method == "id":
        return force_text(order.id)
    elif callable(order_identifier_method):
        return order_identifier_method(order)
    else:
        getter = load(order_identifier_method, "Order identifier generator")
        return getter(order)
