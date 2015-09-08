# -*- coding: utf-8 -*-
from shoop.xtheme.layout import LayoutCell
from shoop.xtheme.views.forms import LayoutCellFormGroup
from shoop_tests.xtheme.utils import plugin_override


def test_pluginless_lcfg():
    with plugin_override():
        cell = LayoutCell(None)
        assert not cell.instantiate_plugin()
        lcfg = LayoutCellFormGroup(layout_cell=cell)
        assert "plugin" not in lcfg.forms


def test_formless_plugin_in_lcfg():
    with plugin_override():
        cell = LayoutCell("inject")
        assert cell.instantiate_plugin()
        lcfg = LayoutCellFormGroup(data={"general-size_md": "8"}, layout_cell=cell)
        assert "plugin" not in lcfg.forms
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.sizes["md"] == 8  # Something got saved even if the plugin doesn't need config


def test_lcfg():
    with plugin_override():
        cell = LayoutCell("text", sizes={"md": 8})
        lcfg = LayoutCellFormGroup(layout_cell=cell)
        assert "general" in lcfg.forms
        assert "plugin" in lcfg.forms
        assert not lcfg.is_valid()  # Oh, we must've forgotten the text...
        lcfg = LayoutCellFormGroup(data={
            "general-size_md": "8",
            "plugin-text": "Hello, world!"
        }, layout_cell=cell)
        assert lcfg.is_valid()  # Let's see now!
        lcfg.save()
        assert cell.sizes["md"] == 8
        assert cell.config["text"] == "Hello, world!"
