# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.pricing import Price, TaxfulPrice, TaxlessPrice
from shuup.utils.money import Money


def test_init():
    TaxfulPrice(42, "EUR")
    TaxlessPrice(42, "EUR")
    assert TaxfulPrice(currency="EUR").value == 0
    assert TaxlessPrice(currency="EUR").value == 0
    with pytest.raises(TypeError):
        Price()
    with pytest.raises(TypeError):
        Price(10)
    with pytest.raises(TypeError):
        Price(10, "EUR")


def test_init_with_currency():
    m42eur = TaxlessPrice(42, "EUR")
    assert m42eur.amount == Money(42, "EUR")
    assert m42eur.value == 42
    assert m42eur.currency == "EUR"

    assert TaxlessPrice(1, "USD").currency == "USD"


def test_tax_mixup():
    with pytest.raises(TypeError):
        TaxfulPrice(42, "EUR") - TaxlessPrice(2, "EUR")


def test_new():
    assert TaxfulPrice(currency="EUR").new(42) == TaxfulPrice(42, "EUR")
    assert TaxlessPrice(currency="EUR").new(-10) == TaxlessPrice(-10, "EUR")
    assert TaxfulPrice(10, "GBP").new(5) == TaxfulPrice(5, "GBP")


def test_add_with_currency():
    for c in ["EUR", "USD", "GBP"]:
        summed = TaxfulPrice(1, c) + TaxfulPrice(2, c)
        assert summed.value == 3
        assert summed.includes_tax == True
        assert summed.currency == c
        assert summed == TaxfulPrice(3, c)
