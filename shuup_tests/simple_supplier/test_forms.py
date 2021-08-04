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
from shuup.simple_supplier.forms import StockAdjustmentForm
from shuup.testing.factories import get_default_product


@pytest.mark.django_db
def test_form(rf, admin_user):
    """
    Test StockAdjustmentForm.
    """
    product = get_default_product()

    partial_sales_unit = SalesUnit.objects.create(identifier="test-sales-partial", decimals=2, name="Partial unit")
    product.sales_unit = partial_sales_unit
    product.save()

    form = StockAdjustmentForm(
        data={
            "purchase_price": 10,
            "delta": 1.2,
        },
        sales_unit=partial_sales_unit,
    )
    assert form.errors == {}
    form.full_clean()
    assert form.cleaned_data["delta"] == Decimal("1.2")

    product2 = get_default_product()
    integer_sales_unit = SalesUnit.objects.create(identifier="test-sales-integer", decimals=0, name="Integer unit")
    product2.sales_unit = integer_sales_unit
    product2.save()

    form = StockAdjustmentForm(
        data={
            "purchase_price": 10,
            "delta": 1.2,
        },
        sales_unit=integer_sales_unit,
    )
    assert form.errors == {}
    form.full_clean()
    assert form.cleaned_data["delta"] == Decimal("1")
