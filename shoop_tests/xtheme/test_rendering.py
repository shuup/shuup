# -*- coding: utf-8 -*-
import pytest

from shoop_tests.xtheme.utils import get_jinja2_engine, get_request, plugin_override


@pytest.mark.parametrize("edit", (False, True))
def test_rendering(edit):
    request = get_request(edit)
    with plugin_override():
        jeng = get_jinja2_engine()
        template = jeng.get_template("complex.jinja")
        output = template.render(request=request)
        assert "wider column" in output
        assert "less wide column" in output
        if edit:
            assert "xt-ph-edit" in output
            assert "data-xt-placeholder-name" in output
            assert "data-xt-row" in output
            assert "data-xt-cell" in output
        # TODO: Should this test be better? No one knows.
