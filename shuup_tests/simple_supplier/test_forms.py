# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal

from shuup.core.models import SalesUnit
from shuup.simple_supplier.forms import AlertLimitForm, StockAdjustmentForm


@pytest.mark.django_db
def test_adjustment_form(rf, admin_user):
    """
    Test StockAdjustmentForm.
    """
    partial_sales_unit = SalesUnit.objects.create(identifier="test-sales-partial", decimals=2, name="Partial unit")
    form = StockAdjustmentForm(
        data={
            "purchase_price": 10,
            "delta": 1.2,
        },
        sales_unit=partial_sales_unit,
    )
    assert form.is_valid()

    integer_sales_unit = SalesUnit.objects.create(identifier="test-sales-integer", decimals=0, name="Integer unit")
    form = StockAdjustmentForm(
        data={
            "purchase_price": 10,
            "delta": 1.2,
        },
        sales_unit=integer_sales_unit,
    )
    assert not form.is_valid()


@pytest.mark.django_db
def test_alet_form(rf, admin_user):
    """
    Test AlertLimitForm.
    """
    partial_sales_unit = SalesUnit.objects.create(identifier="test-sales-partial", decimals=2, name="Partial unit")
    integer_sales_unit = SalesUnit.objects.create(identifier="test-sales-integer", decimals=0, name="Integer unit")

    form = AlertLimitForm(data={"alert_limit": Decimal("10.43")}, sales_unit=partial_sales_unit)
    assert form.is_valid()

    form = StockAdjustmentForm(data={"alert_limit": 1.2}, sales_unit=integer_sales_unit)
    assert not form.is_valid()
