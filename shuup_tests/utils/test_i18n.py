# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import override

from shuup.utils.i18n import get_language_name


def test_get_language_name():
    with override("fi"):
        assert get_language_name("fi") == "suomi"
        assert get_language_name("zh") == "kiina"
        assert get_language_name("zh_Hans") == get_language_name("zh-Hans") == "yksinkertaistettu kiina"
        assert "yksinkertaistettu kiina"

    with override("sv"):
        assert get_language_name("fi") == "finska"
        assert get_language_name("zh") == "kinesiska"
        assert get_language_name("zh_Hans") == get_language_name("zh-Hans") == "förenklad kinesiska"
