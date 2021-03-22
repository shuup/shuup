# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import override_settings

from shuup.core.models import DisplayUnit, SalesUnit
from shuup.core.models._units import SalesUnitAsDisplayUnit


def test_sales_unit_decimals():
    assert SalesUnit(decimals=0).quantity_step == 1
    assert not SalesUnit(decimals=0).allow_fractions
    assert SalesUnit(decimals=1).quantity_step == Decimal("0.1")
    assert SalesUnit(decimals=1).allow_fractions
    assert SalesUnit(decimals=10).quantity_step == Decimal("0.0000000001")
    assert SalesUnit(decimals=2).round("1.509") == Decimal("1.51")
    assert SalesUnit(decimals=0).round("1.5") == Decimal("2")


@pytest.mark.django_db
def test_sales_unit_short_name():
    # test the deprecated compatibility property
    assert SalesUnit(symbol="kg").short_name == "kg"
    assert SalesUnit(short_name="kg").symbol == "kg"
    unit = SalesUnit()
    unit.short_name = "oz"
    assert unit.symbol == "oz"
    en_sales_units = SalesUnit.objects.language("en")
    unit2 = en_sales_units.create(decimals=1, name="Gram", short_name="g")
    assert unit2.name == "Gram"
    assert unit2.symbol == "g"
    unit3 = en_sales_units.get(pk=unit2.pk)
    unit3.set_current_language("en")
    assert unit3.name == "Gram"
    assert unit3.symbol == "g"


@pytest.mark.django_db
@override_settings(**{"LANGUAGES": (("en", "en"), ("fi", "fi"))})
def test_sales_unit_str():
    unit = SalesUnit()
    assert str(unit) == ""

    unit.identifier = "test"
    assert str(unit) == "test"

    unit.set_current_language("en")
    unit.name = "en"
    assert str(unit) == "en"

    unit.set_current_language("fi")
    unit.name = "fi"
    assert str(unit) == "fi"

    unit.set_current_language("en")
    assert unit.name == "en"

    # test fallback
    unit.set_current_language("ja")
    assert unit.name == "en"


@pytest.mark.django_db
def test_sales_unit_display_unit():
    sales_unit = SalesUnit.objects.create()
    assert isinstance(sales_unit.display_unit, SalesUnitAsDisplayUnit)
    display_unit = DisplayUnit.objects.create(internal_unit=sales_unit, default=True)
    assert sales_unit.display_unit == display_unit


@pytest.mark.django_db
def test_display_unit_validator():
    sales_unit = SalesUnit.objects.create()
    display_unit = DisplayUnit(internal_unit=sales_unit, ratio=0)
    with pytest.raises(ValidationError):
        display_unit.full_clean()
