# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from .vat import VatCannotIdentifyValidationError, verify_vat


def validate(tax_number):
    """
    Validate a tax number.

    :param tax_number: Tax number to validate.
    :type tax_number: str
    :return:
      Type identifier of the tax number, if detected.  Possible
      values for now are either "vat" or "unknown".
    :rtype: str

    :raise:
      `ValidationError` if tax number type was detected, but it is
      somehow malformed.
    """
    try:
        # Check if the tax number is a VAT code
        #
        prefix, code_parts = verify_vat(tax_number)
        return "vat" if prefix and code_parts else "unknown"
    except VatCannotIdentifyValidationError:
        # Was not a VAT code, maybe it's some other tax number?
        #
        # Note: verify_vat may raise also VatInvalidValidationError
        # which we intentionally don't catch here, since then it was a
        # VAT, but invalid.
        pass

    return "unknown"
