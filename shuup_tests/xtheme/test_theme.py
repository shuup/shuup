# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.xtheme import (
    get_current_theme, get_theme_by_identifier, set_current_theme
)
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import printable_gibberish
from shuup_tests.xtheme.utils import FauxTheme, FauxTheme2


@pytest.mark.django_db
def test_theme_activation():
    with override_current_theme_class():
        with override_provides("xtheme", [
            "shuup_tests.xtheme.utils:FauxTheme",
            "shuup_tests.xtheme.utils:FauxTheme2"
        ]):
            ThemeSettings.objects.all().delete()
            assert not get_current_theme()
            set_current_theme(FauxTheme.identifier)
            assert isinstance(get_current_theme(), FauxTheme)
            set_current_theme(FauxTheme2.identifier)
            assert isinstance(get_current_theme(), FauxTheme2)
            with pytest.raises(ValueError):
                set_current_theme(printable_gibberish())



@pytest.mark.django_db
def test_theme_settings_api():
    with override_provides("xtheme", [
        "shuup_tests.xtheme.utils:FauxTheme",
        "shuup_tests.xtheme.utils:FauxTheme2"
    ]):
        ThemeSettings.objects.all().delete()
        theme = get_theme_by_identifier(FauxTheme2.identifier)
        theme.set_setting("foo", "bar")
        theme.set_settings(quux=[4, 8, 15, 16, 23, 42])
        theme = get_theme_by_identifier(FauxTheme2.identifier)
        assert theme.get_setting("foo") == "bar"
        assert theme.get_settings() == {
            "foo": "bar",
            "quux": [4, 8, 15, 16, 23, 42]
        }
