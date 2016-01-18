# -*- coding: utf-8 -*-
import pytest

from shoop.xtheme.testing import override_current_theme_class
from shoop_tests.xtheme.utils import (
    FauxTheme, FauxView, get_jinja2_engine, get_request, plugin_override
)


@pytest.mark.django_db
@pytest.mark.parametrize("edit", (False, True))
@pytest.mark.parametrize("injectable", (False, True))
@pytest.mark.parametrize("theme_class", (None, FauxTheme))
def test_rendering(edit, injectable, theme_class):
    request = get_request(edit)
    with override_current_theme_class(theme_class):
        with plugin_override():
            jeng = get_jinja2_engine()
            template = jeng.get_template("complex.jinja")
            view = FauxView()
            view.xtheme_injection = bool(injectable)
            output = template.render(context={
                "view": view,
            }, request=request)
            assert "wider column" in output
            assert "less wide column" in output
            if edit and injectable and theme_class:
                assert "xt-ph-edit" in output
                assert "data-xt-placeholder-name" in output
                assert "data-xt-row" in output
                assert "data-xt-cell" in output
                assert "XthemeEditorConfig" in output
            # TODO: Should this test be better? No one knows.
