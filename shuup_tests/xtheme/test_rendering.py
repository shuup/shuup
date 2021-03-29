# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import mock
import pytest

from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.xtheme.utils import FauxTheme, FauxView, get_jinja2_engine, get_request, plugin_override


@pytest.mark.django_db
@pytest.mark.parametrize("edit", (False, True))
@pytest.mark.parametrize("injectable", (False, True))
@pytest.mark.parametrize("theme_class", (None, FauxTheme))
@pytest.mark.parametrize("global_type", (False, True))
def test_rendering(edit, injectable, theme_class, global_type):
    request = get_request(edit)
    request.resolver_match = mock.Mock()
    request.resolver_match.app_name = "shuup"

    with override_current_theme_class(theme_class):
        with plugin_override():
            jeng = get_jinja2_engine()
            if global_type:
                template = jeng.get_template("global_complex.jinja")
            else:
                template = jeng.get_template("complex.jinja")
            view = FauxView()
            view.xtheme_injection = bool(injectable)
            output = template.render(context={"view": view, "request": request}, request=request)

            # From now on we render placholders in views that
            # actually can be edited.
            if injectable and theme_class:
                assert "wider column" in output
                assert "less wide column" in output

            if edit and injectable and theme_class:
                assert "xt-ph-edit" in output
                assert "data-xt-placeholder-name" in output
                assert "data-xt-row" in output
                assert "data-xt-cell" in output
                assert "XthemeEditorConfig" in output
