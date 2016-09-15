# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.xtheme._theme import override_current_theme_class, get_current_theme
from shuup.xtheme.layout import LayoutCell
from shuup.xtheme.plugins.consts import FALLBACK_LANGUAGE_CODE
from shuup.xtheme.views.forms import (
    LayoutCellFormGroup, LayoutCellGeneralInfoForm
)
from shuup_tests.xtheme.utils import get_request
from shuup_tests.xtheme.utils import plugin_override


def test_pluginless_lcfg():
    with plugin_override():
        with override_current_theme_class(None):
            request = get_request(edit=False)
            theme = get_current_theme(request)
            cell = LayoutCell(theme, None)
            assert not cell.instantiate_plugin()
            lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme)
            assert "plugin" not in lcfg.forms


def test_formless_plugin_in_lcfg():
    two_thirds = int(LayoutCellGeneralInfoForm.CELL_FULL_WIDTH * 2 / 3)
    with plugin_override():
        with override_current_theme_class(None):
            request = get_request(edit=False)
            theme = get_current_theme(request)

            cell = LayoutCell(theme, "inject")
            assert cell.instantiate_plugin()
            lcfg = LayoutCellFormGroup(data={"general-cell_width": "%d" % two_thirds}, layout_cell=cell, theme=theme)

            assert "plugin" not in lcfg.forms
            assert lcfg.is_valid()
            lcfg.save()
            assert cell.sizes["md"] == two_thirds  # Something got saved even if the plugin doesn't need config


def test_lcfg():
    two_thirds = int(LayoutCellGeneralInfoForm.CELL_FULL_WIDTH * 2 / 3)
    with plugin_override():
        with override_current_theme_class(None):
            request = get_request(edit=False)
            theme = get_current_theme(request)

            cell = LayoutCell(theme, "text", sizes={"md": two_thirds, "sm": two_thirds})
            lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme)
            assert "general" in lcfg.forms
            assert "plugin" in lcfg.forms
            assert not lcfg.is_valid()  # Oh, we must've forgotten the text...
            lcfg = LayoutCellFormGroup(data={
                "general-cell_width": "%d" % two_thirds,
                "plugin-text": "Hello, world!"
            }, layout_cell=cell, theme=theme)
            assert lcfg.is_valid()  # Let's see now!
            lcfg.save()
            assert cell.sizes["md"] == two_thirds
            assert cell.config["text"] == {FALLBACK_LANGUAGE_CODE: "Hello, world!"}
