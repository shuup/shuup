# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from decimal import Decimal
from django.utils import translation
from django.utils.translation.trans_real import DjangoTranslation, translation as get_trans

from shuup.core.models import DisplayUnit, PiecesSalesUnit, SalesUnit, UnitInterface
from shuup.core.models._units import SalesUnitAsDisplayUnit


def nbsp(x):
    """
    Convert space to non-breaking space.
    """
    return x.replace(" ", "\xa0")


def test_unit_interface_smoke():
    gram = get_g_in_kg_unit(decimals=4, display_decimals=1)
    assert gram.symbol == "g"
    assert gram.internal_symbol == "kg"
    assert gram.to_display(Decimal("0.01")) == 10
    assert gram.from_display(10) == Decimal("0.01")
    assert gram.render_quantity(Decimal("0.01")) == "10.0g"
    assert gram.comparison_quantity == Decimal("0.1")


def test_unit_interface_init_without_args():
    unit = UnitInterface()
    assert isinstance(unit.internal_unit, PiecesSalesUnit)
    assert isinstance(unit.display_unit, SalesUnitAsDisplayUnit)
    assert unit.display_unit.internal_unit == unit.internal_unit


def test_unit_interface_init_from_internal_unit():
    sales_unit = SalesUnit(name="Test", symbol="tst")
    unit = UnitInterface(sales_unit)
    assert unit.internal_unit == sales_unit
    assert isinstance(unit.display_unit, SalesUnitAsDisplayUnit)
    assert unit.display_unit.internal_unit == sales_unit


def test_unit_interface_init_from_display_unit():
    sales_unit = SalesUnit(name="Test", symbol="tst")
    display_unit = DisplayUnit(name="Test2", symbol="t2", internal_unit=sales_unit)
    unit = UnitInterface(display_unit=display_unit)
    assert unit.display_unit == display_unit
    assert unit.internal_unit == sales_unit


@pytest.mark.django_db
def test_unit_interface_init_with_non_default_display_unit():
    sales_unit = SalesUnit.objects.create(name="Test", symbol="tst")
    default_du = DisplayUnit.objects.create(
        name="Default Display Unit", symbol="ddu", internal_unit=sales_unit, default=True
    )
    non_default_du = DisplayUnit.objects.create(
        name="Non-default Display Unit", symbol="ndu", internal_unit=sales_unit, default=False
    )
    assert sales_unit.display_unit == default_du
    unit = UnitInterface(sales_unit, non_default_du)
    assert unit.internal_unit == sales_unit
    assert unit.display_unit == non_default_du
    assert unit.internal_unit.display_unit == default_du


def test_unit_interface_init_unit_compatibility_check():
    su1 = SalesUnit(identifier="SU1", symbol="su1")
    su2 = SalesUnit(identifier="SU2", symbol="su2")
    du = DisplayUnit(name="DU", symbol="du", internal_unit=su1)
    UnitInterface(su1, du)  # OK
    with pytest.raises(AssertionError) as exc_info:
        UnitInterface(su2, du)
    assert str(exc_info.value) == ("Incompatible units: <SalesUnit:None-SU2>, <DisplayUnit:None>")


def test_unit_interface_display_precision():
    sales_unit = SalesUnit(symbol="t")
    assert UnitInterface(display_unit=DisplayUnit(internal_unit=sales_unit, decimals=9)).display_precision == Decimal(
        "0.000000001"
    )
    assert UnitInterface(display_unit=DisplayUnit(internal_unit=sales_unit, decimals=4)).display_precision == Decimal(
        "0.0001"
    )
    assert UnitInterface(display_unit=DisplayUnit(internal_unit=sales_unit, decimals=2)).display_precision == Decimal(
        "0.01"
    )
    assert UnitInterface(display_unit=DisplayUnit(internal_unit=sales_unit, decimals=0)).display_precision == Decimal(
        "1"
    )


def test_unit_interface_to_display():
    gram3 = get_g_in_kg_unit(decimals=3, display_decimals=0)
    assert gram3.to_display(Decimal("0.01")) == 10
    assert gram3.to_display(Decimal("0.001")) == 1
    assert gram3.to_display(Decimal("0.0005")) == 1
    assert gram3.to_display(Decimal("0.000499")) == 0
    assert gram3.to_display(Decimal("-1")) == -1000
    assert gram3.to_display(Decimal("-0.1234")) == -123
    assert gram3.to_display(Decimal("-0.1235")) == -124


def test_unit_interface_to_display_small_display_prec():
    gram6 = get_g_in_kg_unit(decimals=6, display_decimals=1)
    assert gram6.to_display(Decimal("0.01")) == 10
    assert gram6.to_display(Decimal("0.001")) == 1
    assert gram6.to_display(Decimal("0.0005")) == Decimal("0.5")
    assert gram6.to_display(Decimal("0.000499")) == Decimal("0.5")
    assert gram6.to_display(Decimal("0.0001234")) == Decimal("0.1")
    assert gram6.to_display(Decimal("0.0001235")) == Decimal("0.1")
    assert gram6.to_display(Decimal("12.3456789")) == Decimal("12345.7")


def test_unit_interface_to_display_float():
    gram3 = get_g_in_kg_unit(decimals=3, display_decimals=0)
    assert gram3.to_display(0.01) == 10


def test_unit_interface_to_display_str():
    gram3 = get_g_in_kg_unit(decimals=3, display_decimals=0)
    assert gram3.to_display("0.01") == 10


def test_unit_interface_from_display():
    gram3 = get_g_in_kg_unit(decimals=3, display_decimals=0)
    assert gram3.from_display(1234) == Decimal("1.234")
    assert gram3.from_display(Decimal("123.456")) == Decimal("0.123")
    assert gram3.from_display(Decimal("123.5")) == Decimal("0.124")
    assert gram3.from_display(Decimal("124.5")) == Decimal("0.125")


def test_unit_interface_from_display_small_display_prec():
    gram6 = get_g_in_kg_unit(decimals=6, display_decimals=1)
    assert gram6.from_display(123) == Decimal("0.123")
    assert gram6.from_display(Decimal("123.456")) == Decimal("0.123456")
    assert gram6.from_display(Decimal("123.4565")) == Decimal("0.123457")


def test_unit_interface_from_display_float():
    gram6 = get_g_in_kg_unit(decimals=6, display_decimals=3)
    assert gram6.from_display(123.456) == Decimal("0.123456")


def test_unit_interface_from_display_str():
    gram6 = get_g_in_kg_unit(decimals=6, display_decimals=3)
    assert gram6.from_display("123.456") == Decimal("0.123456")


def test_unit_interface_render_quantity():
    gram3 = get_g_in_kg_unit(decimals=3, display_decimals=0)
    with translation.override("en"):
        assert gram3.render_quantity(123) == "123,000g"
        assert gram3.render_quantity(1234567) == "1,234,567,000g"
        assert gram3.render_quantity(0.123) == "123g"
        assert gram3.render_quantity("0.0521") == "52g"
        assert gram3.render_quantity("0.0525") == "53g"
        assert gram3.render_quantity("0.0535") == "54g"


def test_unit_interface_render_quantity_pieces():
    pcs = UnitInterface(PiecesSalesUnit())
    with translation.override("en"):
        assert pcs.render_quantity(123) == "123"
        assert pcs.render_quantity(1234567) == "1,234,567"
        assert pcs.render_quantity(0.123) == "0"
        assert pcs.render_quantity("52.1") == "52"
        assert pcs.render_quantity("52.5") == "53"
        assert pcs.render_quantity("53.5") == "54"
        assert pcs.render_quantity(123, force_symbol=True) == "123pc."


def test_unit_interface_render_quantity_small_display_prec():
    gram6 = get_g_in_kg_unit(decimals=6, display_decimals=1)
    with translation.override(None):
        assert gram6.render_quantity(Decimal("12.3456789")) == "12345.7g"


def test_unit_interface_render_quantity_translations():
    # Let's override some translations, just to be sure
    for lang in ["en", "pt-br", "hi", "hy"]:
        get_trans(lang).merge(ValueSymbolTranslationWithoutSpace)
    for lang in ["fi"]:
        get_trans(lang).merge(ValueSymbolTranslationWithSpace)

    gram = get_g_in_kg_unit(decimals=7, display_decimals=4)
    qty = Decimal("4321.1234567")
    with translation.override(None):
        assert gram.render_quantity(qty) == "4321123.4567g"
    with translation.override("en"):
        assert gram.render_quantity(qty) == "4,321,123.4567g"
    with translation.override("fi"):
        assert gram.render_quantity(qty) == nbsp("4 321 123,4567g")
    with translation.override("pt-br"):
        assert gram.render_quantity(qty) == "4.321.123,4567g"
    with translation.override("hi"):
        assert gram.render_quantity(qty) == "43,21,123.4567g"
    with translation.override("hy"):
        assert gram.render_quantity(qty) == "4321123,4567g"


trans_key = (
    "Display value with unit symbol (with or without space)" "\x04" "{value}{symbol}"  # Gettext context separator
)


class ValueSymbolTranslationWithSpace(object):
    _fallback = None
    _catalog = {trans_key: nbsp("{value} {symbol}")}
    plural = lambda n: int(n != 1)


class ValueSymbolTranslationWithoutSpace(object):
    _fallback = None
    _catalog = {trans_key: "{value}{symbol}"}
    plural = lambda n: int(n != 1)


def test_unit_interface_render_quantity_internal_kg():
    gram3 = get_g_in_kg_unit(decimals=3, display_decimals=1)
    with translation.override("en"):
        assert gram3.render_quantity_internal(123) == "123.000kg"
        assert gram3.render_quantity_internal(1234567) == "1,234,567.000kg"
        assert gram3.render_quantity_internal(0.123) == "0.123kg"
        assert gram3.render_quantity_internal("0.0521") == "0.052kg"
        assert gram3.render_quantity_internal("0.0525") == "0.053kg"
        assert gram3.render_quantity_internal("0.0535") == "0.054kg"


def test_unit_interface_render_quantity_internal_pieces():
    pcs = UnitInterface(PiecesSalesUnit())
    with translation.override("en"):
        assert pcs.render_quantity_internal(123) == "123"
        assert pcs.render_quantity_internal(1234567) == "1,234,567"
        assert pcs.render_quantity_internal(0.123) == "0"
        assert pcs.render_quantity_internal("52.1") == "52"
        assert pcs.render_quantity_internal("52.5") == "53"
        assert pcs.render_quantity_internal("53.5") == "54"
        assert pcs.render_quantity_internal(123, force_symbol=True) == "123pc."


def test_unit_interface_get_per_values():
    pcs = UnitInterface(PiecesSalesUnit())
    gram = get_g_in_kg_unit(decimals=3, display_decimals=1)
    gram.display_unit.comparison_value = 100
    with translation.override("en"):
        assert pcs.get_per_values() == (1, "")
        assert pcs.get_per_values(force_symbol=True) == (1, "pc.")
        assert gram.get_per_values() == (Decimal("0.1"), "100.0g")


def get_g_in_kg_unit(decimals, display_decimals, comparison=100):
    return UnitInterface(
        display_unit=DisplayUnit(
            internal_unit=get_kilogram_sales_unit(decimals=decimals),
            ratio=Decimal("0.001"),
            decimals=display_decimals,
            symbol="g",
            comparison_value=comparison,
        )
    )


def get_kilogram_sales_unit(decimals):
    return SalesUnit(name="Kilograms", symbol="kg", decimals=decimals)


def test_sales_unit_as_display_unit():
    sales_unit = SalesUnit(decimals=3)
    display_unit = SalesUnitAsDisplayUnit(sales_unit)
    assert display_unit.internal_unit == sales_unit
    assert display_unit.ratio == 1
    assert display_unit.decimals == sales_unit.decimals
    assert display_unit.comparison_value == 1
    assert display_unit.allow_bare_number is False
    assert display_unit.default is False
    assert display_unit.pk is None
    assert display_unit == display_unit

    # Name and symbol should be "lazy" to allow language switch
    sales_unit.set_current_language("en")
    sales_unit.symbol = "Kg"
    sales_unit.name = "Kilogram"
    assert display_unit.name == sales_unit.name
    assert display_unit.symbol == sales_unit.symbol
    assert "{}".format(display_unit) == sales_unit.name
    sales_unit.set_current_language("fi")
    sales_unit.name = "kilogramma"
    sales_unit.symbol = "kg"
    assert display_unit.name == sales_unit.name
    assert display_unit.symbol == sales_unit.symbol
    assert "{}".format(display_unit) == sales_unit.name


def test_sales_unit_as_display_unit_allow_bare_number():
    each = SalesUnit(decimals=0, symbol="ea.")
    kg = SalesUnit(decimals=3, symbol="kg")
    assert SalesUnitAsDisplayUnit(each).allow_bare_number is True
    assert SalesUnitAsDisplayUnit(kg).allow_bare_number is False


def test_pieces_sales_unit():
    pcs = PiecesSalesUnit()
    assert pcs.identifier == "_internal_pieces_unit"
    with translation.override(None):
        assert pcs.name == "Pieces"
        assert pcs.symbol == "pc."
        assert "{}".format(pcs) == "Pieces"
    assert isinstance(pcs.display_unit, SalesUnitAsDisplayUnit)
    assert pcs.display_unit.internal_unit == pcs


def test_kg_in_oz():
    kg_oz = UnitInterface(
        display_unit=DisplayUnit(
            internal_unit=get_kilogram_sales_unit(decimals=9), ratio=Decimal("0.028349523"), decimals=3, symbol="oz"
        )
    )
    assert kg_oz.comparison_quantity == Decimal("0.028349523")
    assert kg_oz.render_quantity("0.028349523") == "1.000oz"
    assert kg_oz.render_quantity(1) == "35.274oz"
    assert kg_oz.render_quantity(0.001) == "0.035oz"
    assert kg_oz.from_display(Decimal("0.001")) == Decimal("0.000028350")
    assert kg_oz.to_display(Decimal("0.000028350")) == approx("0.001")


def approx(value):
    return pytest.approx(Decimal(value), abs=Decimal("0.1") ** 7)
