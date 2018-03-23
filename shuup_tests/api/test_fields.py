# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest
from rest_framework import serializers

from shuup.api.fields import MoneyField
from shuup.core.fields import MONEY_FIELD_DECIMAL_PLACES
from shuup.utils.money import Money


class TestSerializer(serializers.Serializer):
    price = MoneyField()


class FakeModel(object):
    price = None
    def __init__(self, price):
        self.price = price


@pytest.mark.parametrize("value,currency", [
    (13.24, "USD"),
    ("13.24", "BRL"),
    (Decimal(42), "EUR"),
    (-1, "CAD"),
    (2, "USD")
])
def test_money_field_parse_valid(value, currency):
    data = {
        "price": {
            "currency": currency,
            "value": value
        }
    }
    serializer = TestSerializer(data=data)
    assert serializer.is_valid(True)


@pytest.mark.parametrize("value,currency", [
    (13.24, ""),
    ("", ""),
    (None, "EUR")
])
def test_money_field_parse_invalid(value, currency):
    data = {"price": {}}

    if value:
        data["price"]["value"] = value
    if currency:
        data["price"]["currency"] = currency

    serializer = TestSerializer(data=data)
    assert serializer.is_valid() is False


@pytest.mark.parametrize("value,currency", [
    (13.24, "USD"),
    ("13.24", "BRL"),
    (Decimal(42), "EUR"),
    (-1, "CAD"),
    (2, "USD")
])
def test_money_field_serialize(value, currency):
    serializer = TestSerializer(FakeModel(Money(value, currency)))
    precision = Decimal(".1") ** MONEY_FIELD_DECIMAL_PLACES
    assert serializer.data["price"]["value"] == str(Decimal(value).quantize(precision))
    assert serializer.data["price"]["currency"] == currency
