# -*- coding: utf-8 -*-
import pytest
from shoop.apps.provides import override_provides
from shoop.xtheme.models import ThemeSettings
from shoop.xtheme.theme import (
    get_current_theme, set_current_theme, get_theme_by_identifier, override_current_theme_class
)
from shoop_tests.utils import printable_gibberish
from shoop_tests.xtheme.utils import FauxTheme, FauxTheme2


@pytest.mark.django_db
def test_theme_activation():
    with override_current_theme_class():
        with override_provides("xtheme", [
            "shoop_tests.xtheme.utils:FauxTheme",
            "shoop_tests.xtheme.utils:FauxTheme2"
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
        "shoop_tests.xtheme.utils:FauxTheme",
        "shoop_tests.xtheme.utils:FauxTheme2"
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
