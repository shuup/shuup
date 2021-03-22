# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.utils.translation import override

from shuup.core import cache
from shuup.utils.i18n import get_language_name, is_existing_language, remove_extinct_languages

LANGUAGES = {
    0: ("en", True),  # English
    1: ("fi", True),  # Finnish
    2: ("bew", False),  # Betawi
    3: ("bss", False),  # Akoose
    4: ("en_US", False),  # American English
    5: ("is", True),  # Icelandic
    6: ("es_419", False),  # Latin American Spanish
    7: ("nds_NL", False),  # Low Saxon
    8: ("arn", False),  # Mapuche
    9: ("sv", True),  # swedish
    10: ("", False),  # empty.. doh
}


def test_get_language_name_1():
    with override("fi"):
        assert get_language_name("fi") == "suomi"
        assert get_language_name("zh") == "kiina"
        assert get_language_name("zh_Hans") == get_language_name("zh-Hans") == "yksinkertaistettu kiina"
        assert "yksinkertaistettu kiina"


def test_get_language_name_2():
    with override("sv"):
        assert get_language_name("fi") == "finska"
        assert get_language_name("zh") == "kinesiska"
        assert get_language_name("zh_Hans") == get_language_name("zh-Hans") == "förenklad kinesiska"


def test_existing_languages():
    for x in range(11):
        language = LANGUAGES[x][0]
        exists = LANGUAGES[x][1]
        assert is_existing_language(language) == exists


def test_remove_extinct_languages():
    all_languages = [v[0] for k, v in six.iteritems(LANGUAGES)]
    expected = set([v[0] for k, v in six.iteritems(LANGUAGES) if v[1]])
    assert remove_extinct_languages(tuple(all_languages)) == expected
