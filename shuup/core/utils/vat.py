# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import re

import six
from django.core.exceptions import ValidationError

# Patterns from
# https://www.vero.fi/en/detailed-guidance/guidance/48689/vat_numbers_in_eu_member_state/
PATTERNS = {
    "AT": {
        "country": "Austria",
        "iso3166": "AT",
        "pattern": "U99999999",  # Initial always U, then 8 numbers
    },
    "BE": {
        "country": "Belgium",
        "iso3166": "BE",
        "pattern": "9999999999",  # 1 block of 10 digits
    },
    "BG": {
        "country": "Bulgaria",
        "iso3166": "BG",
        "pattern": [
            "999999999",  # 1 block of 9 digits
            "9999999999",  # 1 block of 10 digits
        ]
    },
    "CY": {
        "country": "Cyprus",
        "iso3166": "CY",
        "pattern": "99999999L",  # 1 block of 9 characters
    },
    "CZ": {
        "country": "Czech Republic",
        "iso3166": "CZ",
        "pattern": [
            "99999999",
            "999999999",
            "9999999999"
        ]
    },
    "DE": {
        "country": "Germany",
        "iso3166": "DE",
        "pattern": "999999999",  # 1 block of 9 digits
    },
    "DK": {
        "country": "Denmark",
        "iso3166": "DK",
        "pattern": "99999999",  # 4 blocks of 2 digits
    },
    "EE": {
        "country": "Estonia",
        "iso3166": "EE",
        "pattern": "999999999",  # 1 block of 9 digits
    },
    "EL": {
        "iso3166": "GR",
        "country": "Greece",
        "pattern": "999999999",  # 1 block of 9 digits
    },
    "ES": {
        "country": "Spain",
        "iso3166": "ES",
        "pattern": [
            "X9999999X4",  # 1 block of 9 characters
            "X99999999",
            "99999999X",
            "X9999999X"
        ]
        # CIF (Certificado de Identificación Fiscal): This is the tax ID number for all companies.
        # It consists of a letter followed by 8 digits. The letter represents the type of company,
        # the most common being an 'A' for Sociedad Anónima or a 'B' for Sociedad Limitada.
        # For companies nonresident in Spain, the letter is 'N'.
        # VAT number (Número IVA): This is 'ES' followed by the CIF.

        # From vero.fi. 9 characters where first or last can be chars or number, but can not be
        # numbers.
    },
    "FI": {
        "country": "Finland",
        "iso3166": "FI",
        "pattern": "99999999",  # 1 block of 8 digits
    },
    "FR": {
        "country": "France",
        "iso3166": "FR",
        "pattern": "XX999999999",  # 1 block of 2 characters, 1 block of 9 digits
    },
    "GB": {
        "country": "United Kingdom",
        "iso3166": "GB",
        "pattern": [
            "999999999",  # 1 block of 9 or 12 digits
            "999999999999",
            "GD999",
            "HA999"
        ]
    },
    "HU": {
        "iso3166": "HU",
        "country": "Hungary",
        "pattern": "99999999",  # 1 block of 8 digits
    },
    "HR": {
        "iso3166": "HR",
        "country": "Croatia",
        "pattern": "99999999999",  # 1 block of 11 digits
    },
    "IE": {
        "iso3166": "IE",
        "country": "Ireland",
        "pattern": [
            "9S99999L",  # 1 block of 8 or 9 characters
            "9999999LL"
        ]
    },
    "IT": {
        "iso3166": "IT",
        "country": "Italy",
        "pattern": "99999999999",  # 1 block of 11 digits
    },
    "LT": {
        "iso3166": "LT",
        "country": "Lithuania",
        "pattern": [
            "999999999",
            "999999999999",  # 1 block of 9 digits, or 1 block of 12 digits
        ]
    },
    "LU": {
        "iso3166": "LU",
        "country": "Luxembourg",
        "pattern": "99999999",  # 1 block of 8 digits
    },
    "LV": {
        "country": "Latvia",
        "iso3166": "LV",
        "pattern": "99999999999",  # 1 block of 11 digits
    },
    "MT": {
        "country": "Malta",
        "iso3166": "MT",
        "pattern": "99999999",  # 1 block of 8 digits
    },
    "NL": {
        "country": "The Netherlands",
        "iso3166": "NL",
        "pattern": "999999999B99",  # 1 block of 12 characters. From vero.fi tenth char after country code is allways B
    },
    "PL": {
        "country": "Poland",
        "iso3166": "PL",
        "pattern": "9999999999",  # 1 block of 10 digits
    },
    "PT": {
        "country": "Portugal",
        "iso3166": "PT",
        "pattern": "999999999",  # 1 block of 9 digits
    },
    "RO": {
        "country": "Romania",
        "iso3166": "RO",
        "pattern": "99R",  # 1 block of minimum 2 digits and maximum 10 digits
    },
    "SE": {
        "country": "Sweden",
        "iso3166": "SE",
        "pattern": "999999999901",  # 1 block of 12 digits. From vero.fi 2 last digits is allways 01
    },
    "SI": {
        "country": "Slovenia",
        "iso3166": "SI",
        "pattern": "99999999",  # 1 block of 8 digits
    },
    "SK": {
        "country": "Slovakia",
        "iso3166": "SK",
        "pattern": "9999999999",  # 1 block of 10 digits
    },
}


# *: Format excludes 2 letter alpha prefix
# 9: A digit
# X: A letter or a digit
# S: A letter; a digit; "+" or "*"
# L: A letter


def compile_pattern(prefix, pattern):
    r = pattern.replace(" ", "")
    for gf, gt in (
            ("9", "[0-9]"),
            ("R", "[0-9]*"),
            ("X", "[a-z0-9]"),
            ("S", "[a-z0-9+*]"),
            ("L", "[a-z]"),
    ):
        regex_frag = "(%s{%%d})" % gt

        def gt(m):
            return (regex_frag % len(m.group(0)))

        r = re.sub(gf + "+", gt, r)

    return re.compile("^" + prefix + r + "$", re.I)


class VatValidationError(ValidationError):
    code = None

    def __init__(self, *args, **kwargs):
        code = kwargs.pop("code", self.code)
        super(VatValidationError, self).__init__(*args, code=code, **kwargs)


class VatCannotIdentifyValidationError(VatValidationError):
    code = "vat_cannot_identify"


class VatInvalidValidationError(VatValidationError):
    code = "vat_invalid"


def verify_vat(vat_id, default_prefix=""):
    """ Verify an EU VAT ID.

    Returns a tuple (prefix, code_parts) -- if both are truthy, the validation succeeded.
    If the prefix part is falsy, then the prefix was unknown and no validation was even attempted.
    If the prefix part is truthy, then it will contain the country prefix used for validation.
    The code_parts part can still be falsy, if the validation for the country's VAT number pattern failed.

    :param vat_id: The VAT ID string to validate.
    :type vat_id: str
    :param default_prefix: The default prefix to assume if none can be parsed.
    :type default_prefix: str
    :return: Tuple of (prefix, code_parts)
    """

    # Normalize the VAT ID a little bit...
    vat_id = re.sub(r"\s+", "", vat_id.upper())
    vat_id = vat_id.replace("-", "")  # TODO: Not sure if this is a good idea

    prefix = vat_id[:2]
    if prefix not in PATTERNS:  # Okay, it's unknown thus far, so try again with the default prefix if any
        prefix = default_prefix

    # Then see if we know about this prefix.
    spec = PATTERNS.get(prefix)
    if not spec or not prefix:  # Sorry, no dice. :/
        raise VatCannotIdentifyValidationError("VAT ID could not be identified")

    if not vat_id.startswith(prefix):  # Add the prefix back into the VAT if required
        vat_id = prefix + vat_id

    # Get the relephant PATTERNS (one or more) from the spec
    patterns = (spec.get("pattern") or [])
    if isinstance(patterns, six.string_types):
        patterns = [patterns]

    for pat in patterns:
        regexp = compile_pattern(prefix, pat)  # Prefix will be added to the resulting spec.
        match = regexp.match(vat_id)
        if match:
            return (prefix, match.groups())

    raise VatInvalidValidationError(
        "VAT ID for %(country)s could not be validated" % spec)


def get_vat_prefix_for_country(iso3166):
    iso3166 = six.text_type(iso3166).upper()
    for prefix, data in six.iteritems(PATTERNS):  # pragma: no branch
        if data.get("iso3166") == iso3166:
            return prefix
