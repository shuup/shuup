# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from decimal import Decimal

from shuup.core.models import Tax
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.core.taxing.utils import calculate_compounded_added_taxes
from shuup.utils.money import Money


def tax(code, rate=None, amount=None):
    return Tax(code=code, name=("Tax " + code), rate=rate, amount=amount)


def tfprice(value):
    return TaxfulPrice(value, "USD")


def tlprice(value):
    return TaxlessPrice(value, "USD")


def money(value):
    return Money(value, "USD")


@pytest.mark.parametrize("price", [tlprice("123.00"), tfprice("123.00")])
def test_compounded_added_taxes_empty(price):
    result = calculate_compounded_added_taxes(price, [])
    assert result.taxful == tfprice(123)
    assert result.taxless == tlprice(123)
    assert result.taxes == []

    result2 = calculate_compounded_added_taxes(price, [[]])
    assert result2.taxful == tfprice(123)
    assert result2.taxless == tlprice(123)
    assert result2.taxes == []


@pytest.mark.parametrize("price", [tlprice("100.00"), tfprice("115.00")])
def test_compounded_added_taxes_simple(price):
    taxes = [[tax("15%", rate=Decimal("0.15"))]]
    result = calculate_compounded_added_taxes(price, taxes)
    assert result.taxful == tfprice("115")
    assert result.taxless == tlprice("100")
    assert len(result.taxes) == 1
    assert result.taxes[0].tax.code == "15%"
    assert result.taxes[0].amount == money("15")
    assert result.taxes[0].base_amount == money("100")


@pytest.mark.parametrize("price", [tlprice("100.00"), tfprice("121.00")])
def test_compounded_added_taxes_simple_added(price):
    taxes = [
        [
            tax("15%", rate=Decimal("0.15")),
            tax("5%", rate=Decimal("0.05")),
            tax("1%", rate=Decimal("0.01")),
        ]
    ]
    result = calculate_compounded_added_taxes(price, taxes)
    assert result.taxful == tfprice("121")
    assert result.taxless == tlprice("100")
    assert len(result.taxes) == 3
    assert result.taxes[0].tax.code == "15%"
    assert result.taxes[0].amount == money("15")
    assert result.taxes[0].base_amount == money("100")
    assert result.taxes[1].tax.code == "5%"
    assert result.taxes[1].amount == money("5")
    assert result.taxes[1].base_amount == money("100")
    assert result.taxes[2].tax.code == "1%"
    assert result.taxes[2].amount == money("1")
    assert result.taxes[2].base_amount == money("100")


@pytest.mark.parametrize("price", [tlprice("100.00"), tfprice("121.9575")])
def test_compounded_added_taxes_simple_compound(price):
    taxes = [
        [tax("15%", rate=Decimal("0.15"))],
        [tax("5%", rate=Decimal("0.05"))],
        [tax("1%", rate=Decimal("0.01"))],
    ]
    result = calculate_compounded_added_taxes(price, taxes)
    assert result.taxful == tfprice("121.9575")
    assert result.taxless == tlprice("100")
    assert len(result.taxes) == 3
    assert result.taxes[0].tax.code == "15%"
    assert result.taxes[0].amount == money("15")
    assert result.taxes[0].base_amount == money("100")
    assert result.taxes[1].tax.code == "5%"
    assert result.taxes[1].amount == money("5.75")
    assert result.taxes[1].base_amount == money("115")
    assert result.taxes[2].tax.code == "1%"
    assert result.taxes[2].amount == money("1.2075")
    assert result.taxes[2].base_amount == money("120.75")


COMPLEX_TAX_GROUPS = [
    [
        tax("1A", rate=Decimal("0.5")),
        tax("1B", rate=Decimal("0.24")),
        tax("1C", amount=money("1.11")),
        tax("1D", amount=money("0.89")),
    ],
    [
        tax("2A", rate=Decimal("0.1")),
        tax("2B", rate=Decimal("0.01")),
        tax("2C", amount=money("1.25")),
        tax("2D", amount=money("0.25")),
    ],
    [
        tax("3A", amount=money("0.123")),
    ],
    [
        tax("4A", rate=Decimal("0.1")),
    ],
]


@pytest.mark.parametrize("price", [tlprice("100"), tfprice("216.6813")])
def test_compounded_added_taxes_complex(price):
    result = calculate_compounded_added_taxes(price, COMPLEX_TAX_GROUPS)
    result_taxes = [(line_tax.tax.code, line_tax.amount, line_tax.base_amount) for line_tax in result.taxes]
    expected_taxes = [
        # code, tax_amount, base_amount
        ("1A", money("50.0"), money("100")),
        ("1B", money("24.00"), money("100")),
        ("1C", money("1.11"), money("100")),
        ("1D", money("0.89"), money("100")),
        ("2A", money("17.60"), money("176.0")),
        ("2B", money("1.760"), money("176.0")),
        ("2C", money("1.25"), money("176.0")),
        ("2D", money("0.25"), money("176.0")),
        ("3A", money("0.123"), money("196.860")),
        ("4A", money("19.6983"), money("196.983")),
    ]
    assert result_taxes == expected_taxes
    assert result.taxless == tlprice("100")
    assert result.taxful == tfprice("216.6813")


@pytest.mark.parametrize(
    "prices",
    [
        (tlprice("12345.6789"), tfprice("26233.115950206")),
        (tlprice("10000.00"), tfprice("21249.6273")),
        (tlprice("100.00"), tfprice("216.6813")),
        (tlprice("12.97"), tfprice("31.7825838")),
        (tlprice("10.00"), tfprice("25.4727")),
        (tlprice("1.00"), tfprice("6.35184")),
        (tlprice("0.03"), tfprice("4.2910362")),
        (tlprice("0.02"), tfprice("4.2697908")),
        (tlprice("0.01"), tfprice("4.2485454")),
        (tlprice("0.00"), tfprice("4.2273")),
        (tlprice("-1.00"), tfprice("2.10276")),
        (tlprice("-1.9897483"), tfprice("0.000000146718")),
        (tlprice("-10.00"), tfprice("-17.0181")),
    ],
)
def test_compounded_added_taxes_complex2(prices):
    (taxless_price, taxful_price) = prices

    res1 = calculate_compounded_added_taxes(taxless_price, COMPLEX_TAX_GROUPS)
    assert res1.taxless == taxless_price
    assert res1.taxful == taxful_price

    res2 = calculate_compounded_added_taxes(taxful_price, COMPLEX_TAX_GROUPS)
    assert res2.taxless == taxless_price
    assert res2.taxful == taxful_price
