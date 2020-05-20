# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.utils.encoding import force_text

from shuup.utils.importing import load

from ._counters import Counter, CounterType


def calc_reference_number_checksum(rn):
    muls = (7, 3, 1)
    s = 0
    for i, ch in enumerate(rn[::-1]):
        s += muls[i % 3] * int(ch)
    s = 10 - (s % 10)
    return force_text(s)[-1]


def get_unique_reference_number(shop, id):
    from shuup import configuration
    from shuup.admin.modules.settings.consts import ORDER_REFERENCE_NUMBER_LENGTH_FIELD
    now = datetime.datetime.now()
    ref_length = configuration.get(shop, ORDER_REFERENCE_NUMBER_LENGTH_FIELD, settings.SHUUP_REFERENCE_NUMBER_LENGTH)
    dt = ("%06s%07d%04d" % (now.strftime("%y%m%d"), now.microsecond, id % 1000)).rjust(ref_length, "0")
    return dt + calc_reference_number_checksum(dt)


def get_unique_reference_number_for_order(order):
    return get_unique_reference_number(order.shop, order.pk)


def get_running_reference_number(order):
    from shuup import configuration
    from shuup.admin.modules.settings.consts import (ORDER_REFERENCE_NUMBER_PREFIX_FIELD,
                                                     ORDER_REFERENCE_NUMBER_LENGTH_FIELD)
    value = Counter.get_and_increment(CounterType.ORDER_REFERENCE)
    prefix = "%s" % configuration.get(
        order.shop, ORDER_REFERENCE_NUMBER_PREFIX_FIELD, settings.SHUUP_REFERENCE_NUMBER_PREFIX)
    ref_length = configuration.get(
        order.shop, ORDER_REFERENCE_NUMBER_LENGTH_FIELD, settings.SHUUP_REFERENCE_NUMBER_LENGTH)

    padded_value = force_text(value).rjust(ref_length - len(prefix), "0")
    reference_no = "%s%s" % (prefix, padded_value)
    return reference_no + calc_reference_number_checksum(reference_no)


def get_shop_running_reference_number(order):
    from shuup import configuration
    from shuup.admin.modules.settings.consts import ORDER_REFERENCE_NUMBER_LENGTH_FIELD
    value = Counter.get_and_increment(CounterType.ORDER_REFERENCE)
    prefix = "%06d" % order.shop.pk
    ref_length = configuration.get(
        order.shop, ORDER_REFERENCE_NUMBER_LENGTH_FIELD, settings.SHUUP_REFERENCE_NUMBER_LENGTH)
    padded_value = force_text(value).rjust(ref_length - len(prefix), "0")
    reference_no = "%s%s" % (prefix, padded_value)
    return reference_no + calc_reference_number_checksum(reference_no)


def get_reference_number(order):
    from shuup import configuration
    from shuup.admin.modules.settings.consts import ORDER_REFERENCE_NUMBER_METHOD_FIELD

    if order.reference_number:
        raise ValueError("Error! Order passed to function `get_reference_number()` already has a reference number.")
    reference_number_method = configuration.get(
        order.shop, ORDER_REFERENCE_NUMBER_METHOD_FIELD, settings.SHUUP_REFERENCE_NUMBER_METHOD)
    if reference_number_method == "unique":
        return get_unique_reference_number_for_order(order)
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
        raise ValueError("Error! Order passed to function `get_order_identifier()` already has an identifier.")
    order_identifier_method = settings.SHUUP_ORDER_IDENTIFIER_METHOD
    if order_identifier_method == "id":
        return force_text(order.id)
    elif callable(order_identifier_method):
        return order_identifier_method(order)
    else:
        getter = load(order_identifier_method, "Order identifier generator")
        return getter(order)
