# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.utils.tax_numbers import validate
from shuup.core.utils.vat import VatInvalidValidationError


@pytest.mark.django_db
def test_tax_numbers():
    TAX_NUMBERS_TO_VALIDATE = [
        ("12345", False, False),
        ("FI12345678", True, True),
        ("FI123456781", True, False),
        ("GBHA999", True, True),
        ("GBHA9999", True, False),
    ]
    for tax_number, is_vat, is_valid in TAX_NUMBERS_TO_VALIDATE:
        if is_vat:
            if is_valid:
                assert validate(tax_number) == "vat"
            else:
                with pytest.raises(VatInvalidValidationError):
                    validate(tax_number)
        else:
            assert validate(tax_number) == ("vat" if is_valid else "unknown")
