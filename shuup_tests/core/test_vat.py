# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError

from shuup.core.utils.vat import get_vat_prefix_for_country, verify_vat


@pytest.mark.parametrize(
    "input, expected",
    [
        ("FI 12345678", ("12345678",)),
        ("FI12345678", ("12345678",)),
        ("ESW0303010U4", ("W", "0303010", "U")),  # Technically correct
        ("ATU44360204", ("44360204",)),  # Julius Meinl am Graben GmbH
    ],
)
def test_vat_valid(input, expected):
    prefix, result = verify_vat(input)
    assert result == expected, "%s works" % input


@pytest.mark.parametrize(
    "input, expected_code",
    [
        ("FIURMOM", "vat_invalid"),  # Not a valid Finnish VAT code
        ("NL XYZ66603", "vat_invalid"),
        ("DSFARGEG", "vat_cannot_identify"),
        ("ATU999999991", "vat_invalid"),  # Too long
    ],
)
def test_vat_invalid(input, expected_code):
    with pytest.raises(ValidationError) as excinfo:
        verify_vat(input)
    assert excinfo.value.code == expected_code


def test_vat_autoprefix():
    prefix, result = verify_vat("12345678", "FI")
    assert prefix == "FI"
    assert result == ("12345678",)


def test_vat_prefix_for_country():
    prefix, result = verify_vat("12345678", get_vat_prefix_for_country("fi"))
    assert prefix == "FI"
    assert result == ("12345678",)
