# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal

from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.utils.money import Money
from shuup.utils.numbers import UnitMixupError
from shuup.utils.properties import (
    MoneyProperty,
    MoneyPropped,
    PriceProperty,
    TaxfulPriceProperty,
    TaxlessPriceProperty,
    resolve,
)


def test_resolve():
    class X:
        pass

    x = X()
    x.y = X()
    x.y.z = X()
    x.y.z.t = 42
    x.a = 1
    b = 2

    assert resolve(x, "y.z.t") == 42
    assert resolve(x, "a") == 1
    assert resolve(b, "") == 2


def get_wallet():
    class Wallet(object):
        amount = MoneyProperty("value", "currency")

        def __init__(self):
            self.value = 42
            self.currency = "EUR"

    return Wallet()


def test_money_property_get():
    w = get_wallet()
    assert w.amount == Money(42, "EUR")


def test_money_property_set():
    w = get_wallet()
    w.amount = Money(3, "EUR")
    assert w.amount == Money(3, "EUR")
    assert w.value == 3
    assert type(w.value) == Decimal
    assert w.currency == "EUR"


def test_money_property_set_invalid_unit():
    w = get_wallet()
    with pytest.raises(UnitMixupError):
        w.amount = Money(3, "USD")


def get_market():
    class Market(object):
        price = PriceProperty("value", "currency", "includes_tax")

        def __init__(self):
            self.value = 123
            self.currency = "GBP"
            self.includes_tax = True

    return Market()


def test_price_property_get():
    m = get_market()
    assert m.price == TaxfulPrice(123, "GBP")


def test_price_property_set():
    m = get_market()
    m.price = TaxfulPrice(321, "GBP")
    assert m.price == TaxfulPrice(321, "GBP")
    assert m.value == 321
    assert type(m.value) == Decimal
    assert m.currency == "GBP"


def test_price_property_set_invalid_unit():
    m = get_market()
    with pytest.raises(UnitMixupError):
        m.price = TaxlessPrice(3, "GBP")
    with pytest.raises(UnitMixupError):
        m.price = TaxfulPrice(3, "USD")


def test_taxless_and_taxful_price_properties():
    class Foo(object):
        taxful_value = 110
        taxless_value = 100
        currency = "USD"

        taxful_price = TaxfulPriceProperty("taxful_value", "currency")
        taxless_price = TaxlessPriceProperty("taxless_value", "currency")

    foo = Foo()

    assert foo.taxful_price == TaxfulPrice(110, "USD")
    foo.taxful_price = TaxfulPrice(220, "USD")
    assert foo.taxful_price == TaxfulPrice(220, "USD")
    assert foo.taxful_value == 220

    assert foo.taxless_price == TaxlessPrice(100, "USD")
    foo.taxless_price = TaxlessPrice(200, "USD")
    assert foo.taxless_price == TaxlessPrice(200, "USD")
    assert foo.taxless_value == 200

    with pytest.raises(UnitMixupError):
        foo.taxful_price = TaxlessPrice(220, "USD")

    with pytest.raises(UnitMixupError):
        foo.taxful_price = TaxfulPrice(220, "EUR")

    with pytest.raises(UnitMixupError):
        foo.taxless_price = TaxfulPrice(220, "USD")

    with pytest.raises(UnitMixupError):
        foo.taxless_price = TaxlessPrice(220, "EUR")


class Base(object):
    def __init__(self, **kwargs):
        for (k, v) in kwargs.items():
            setattr(self, k, v)


class Foo(Base):
    pass


class FooItem(MoneyPropped, Base):
    price = PriceProperty("value", "foo.currency", "foo.includes_tax")


def test_money_propped_basic():
    foo = Foo(currency="EUR", includes_tax=True)
    item = FooItem(foo=foo, price=TaxfulPrice(42, "EUR"))
    assert item.price == TaxfulPrice(42, "EUR")
    assert item.value == 42
    assert item.foo.currency == "EUR"


def test_money_propped_type_checking_currency():
    foo = Foo(currency="EUR", includes_tax=True)
    with pytest.raises(TypeError):
        FooItem(foo=foo, price=TaxfulPrice(42, "USD"))


def test_money_propped_type_checking_taxness():
    foo = Foo(currency="EUR", includes_tax=True)
    with pytest.raises(TypeError):
        FooItem(foo=foo, price=TaxlessPrice(42, "EUR"))


def test_money_propped_type_checking_decimal():
    foo = Foo(currency="EUR", includes_tax=True)
    with pytest.raises(TypeError):
        FooItem(foo=foo, price=42)
