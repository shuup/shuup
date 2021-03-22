# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal, InvalidOperation
from django import forms
from django.core.exceptions import ValidationError
from django.db.backends.utils import format_number

from shuup.admin.forms.fields import PercentageField


def test_percentage_field():
    field = PercentageField(min_value=0, max_value=Decimal("0.7"))
    assert Decimal(str(field.widget.attrs["max"])) == 70
    assert field.to_python("50") == Decimal("0.5")
    assert field.to_python(50) == Decimal("0.5")
    assert field.to_python(500) == Decimal(5)
    assert field.to_python("") is None
    assert field.prepare_value(Decimal("0.50")) == 50
    with pytest.raises(ValidationError):
        field.clean(-7)  # --> -0.07 (< min_value)
    with pytest.raises(ValidationError):
        field.clean("700")  # -> 7 (> max_value)

    frm = forms.Form(data={"x": "15"})
    frm.fields["x"] = field
    frm.full_clean()

    assert frm.cleaned_data["x"] == Decimal("0.15")


def test_rounding():
    with pytest.raises(InvalidOperation):
        format_number(Decimal("99.99990"), 6, 5)
    format_number(Decimal("99.9999"), 6, 4)
