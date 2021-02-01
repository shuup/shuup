# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import re
import unicodedata

from django.utils.encoding import force_str, force_text

__all__ = (
    "camel_case",
    "flatten",
    "identifierify",
    "kebab_case",
    "snake_case",
    "space_case",
)

WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)
WORD_SEP_RE = re.compile(r"[\s_-]+", re.UNICODE)


def flatten(str, whitespace="-"):
    """
    Flatten the given text into lowercase ASCII, removing diacriticals etc.
    Replace runs of whitespace with the given whitespace replacement.

    >>> print(flatten("hellö, wörld"))
    hello,-world

    :param str: The string to massage
    :type str: str
    :param whitespace: The string to replace whitespace with
    :type whitespace: str
    :return: A flattened string
    :rtype: str
    """
    str = force_text(str).strip().lower()
    str = force_text(unicodedata.normalize("NFKD", str).encode("ascii", "ignore"))
    str = re.sub(WHITESPACE_RE, whitespace, str)
    return str


def identifierify(value, sep="_"):
    """
    Identifierify the given text (keep only alphanumerics and the given separator(s).

    :param value: The text to identifierify
    :type value: str
    :param sep: The separator(s) to keep
    :type sep: str
    :return: An identifierified string
    :rtype: str
    """
    return "".join(c for c in value if c.isalnum() or c in sep)


def snake_case(value):
    """
    Snake_case the given value (join words with underscores).
    No other treatment is done; use `identifierify` for that.
    """
    return "_".join(s.lower() for s in WORD_SEP_RE.split(force_text(value)) if s)


def kebab_case(value):
    """
    Kebab-case the given value (join words with dashes).
    No other treatment is done; use `identifierify` for that.
    """
    return "-".join(s.lower() for s in WORD_SEP_RE.split(force_text(value)) if s)


def camel_case(value):
    """
    CamelCase the given value (join capitalized words).
    No other treatment is done; use `identifierify` for that.
    """
    return "".join(s.title() for s in WORD_SEP_RE.split(force_text(value)) if s)


def space_case(value):
    """
    Space case the given value (join words that may have been otherwise separated
    with spaces).
    No other treatment is done; use `identifierify` for that.
    """
    return " ".join(s.lower() for s in WORD_SEP_RE.split(force_text(value)) if s)


def force_ascii(string, method='backslashreplace'):
    """
    Force given string to ASCII str.

    :param string: String to convert
    :type string: str|unicode|bytes
    :param method:
      How to handle non-ASCII characters.  Accepted values are
      'backslashreplace' (default), 'xmlcharrefreplace', 'replace' and
      'ignore'.
    :type method: str
    :rtype: str
    """
    return force_str(force_text(string).encode('ascii', errors=method))
