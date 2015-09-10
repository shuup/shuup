# -*- coding: utf-8 -*-
import hashlib

import pytest
from contextlib import contextmanager
from django.template.base import TemplateDoesNotExist
from shoop.apps.provides import override_provides, get_provide_objects
from shoop.xtheme.models import ThemeSettings
from shoop.xtheme.theme import set_current_theme
from shoop_tests.xtheme.utils import get_jinja2_engine


@contextmanager
def noop():
    yield


@pytest.mark.django_db
def test_theme_selection():
    """
    Test that a theme with a `template_dir` actually affects template directory selection.
    """
    with override_provides("xtheme", [
        "shoop_tests.xtheme.utils:FauxTheme",
        "shoop_tests.xtheme.utils:FauxTheme2",
        "shoop_tests.xtheme.utils:H2G2Theme",
    ]):
        ThemeSettings.objects.all().delete()
        for theme in get_provide_objects("xtheme"):
            set_current_theme(theme.identifier)
            je = get_jinja2_engine()
            wrapper = (noop() if theme.identifier == "h2g2" else pytest.raises(TemplateDoesNotExist))
            with wrapper:
                t = je.get_template("42.jinja")
                content = t.render().strip()
                # I'm very aware this is sort of silly, but it's also harmless.
                # I mean, harmless -- not even mostly harmless!
                hex = hashlib.sha1(content.encode("UTF-8")).hexdigest()
                assert hex.count("42") == 5

