# -*- coding: utf-8 -*-
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
