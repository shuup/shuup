# -*- coding: utf-8 -*-
from shuup.xtheme.layout import LayoutCell
from shuup.xtheme.plugins.consts import FALLBACK_LANGUAGE_CODE
from shuup.xtheme.views.forms import (
    LayoutCellFormGroup, LayoutCellGeneralInfoForm
)
from shuup_tests.xtheme.utils import plugin_override


def test_pluginless_lcfg():
    with plugin_override():
        cell = LayoutCell(None)
        assert not cell.instantiate_plugin()
        lcfg = LayoutCellFormGroup(layout_cell=cell)
        assert "plugin" not in lcfg.forms


def test_formless_plugin_in_lcfg():
    two_thirds = int(LayoutCellGeneralInfoForm.CELL_FULL_WIDTH * 2 / 3)
    with plugin_override():
        cell = LayoutCell("inject")
        assert cell.instantiate_plugin()
        lcfg = LayoutCellFormGroup(data={"general-cell_width": "%d" % two_thirds}, layout_cell=cell)
        assert "plugin" not in lcfg.forms
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.sizes["md"] == two_thirds  # Something got saved even if the plugin doesn't need config


def test_lcfg():
    two_thirds = int(LayoutCellGeneralInfoForm.CELL_FULL_WIDTH * 2 / 3)
    with plugin_override():
        cell = LayoutCell("text", sizes={"md": two_thirds, "sm": two_thirds})
        lcfg = LayoutCellFormGroup(layout_cell=cell)
        assert "general" in lcfg.forms
        assert "plugin" in lcfg.forms
        assert not lcfg.is_valid()  # Oh, we must've forgotten the text...
        lcfg = LayoutCellFormGroup(data={
            "general-cell_width": "%d" % two_thirds,
            "plugin-text": "Hello, world!"
        }, layout_cell=cell)
        assert lcfg.is_valid()  # Let's see now!
        lcfg.save()
        assert cell.sizes["md"] == two_thirds
        assert cell.config["text"] == {FALLBACK_LANGUAGE_CODE: "Hello, world!"}
