# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six

from shuup.xtheme.layout import Layout, LayoutCell
from shuup.xtheme.plugins.text import TextPlugin
from shuup.xtheme.rendering import get_view_config, render_placeholder
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import printable_gibberish
from shuup_tests.xtheme.utils import (
    FauxTheme,
    FauxView,
    close_enough,
    get_jinja2_engine,
    get_request,
    get_test_template_bits,
    layout_override,
    plugin_override,
)


def test_layout_serialization():
    theme = FauxTheme
    with plugin_override():
        l = Layout(theme, "test")
        l.begin_column({"md": 8})
        l.add_plugin("text", {"text": "yes"})
        serialized = l.serialize()
        expected = {
            "name": "test",
            "rows": [{"cells": [{"config": {"text": "yes"}, "plugin": "text", "sizes": {"md": 8}}]}],
        }
        assert serialized == expected
        assert Layout.unserialize(theme, serialized).serialize() == expected


def test_layout_rendering(rf):
    request = get_request(edit=False)
    with override_current_theme_class(None):
        with plugin_override():
            with layout_override():
                (template, layout, gibberish, ctx) = get_test_template_bits(request)
                result = six.text_type(render_placeholder(ctx, "test", layout, "test"))
                expect = (
                    """
                <div class="placeholder-edit-wrap">
                <div class="xt-ph" id="xt-ph-test">
                <div class="row xt-ph-row">
                <div class="col-md-12 hidden-xs xt-ph-cell"><p>%s</p></div>
                </div>
                </div>
                </div>
                """
                    % gibberish
                )
                assert close_enough(result, expect)


def test_layout_rendering_with_global_type(rf):
    request = get_request(edit=False)
    with override_current_theme_class(None):
        with plugin_override():
            jeng = get_jinja2_engine()
            template = jeng.from_string("")

            (template, layout, gibberish, ctx) = get_test_template_bits(request)

            global_class = "xt-global-ph"
            result = six.text_type(render_placeholder(ctx, "test", layout, template.template.name, global_type=True))
            assert global_class in result

            result = six.text_type(render_placeholder(ctx, "test", layout, template.template.name, global_type=False))
            assert global_class not in result


def test_layout_edit_render():
    request = get_request(edit=True)
    with override_current_theme_class(None):
        with plugin_override():
            (template, layout, gibberish, ctx) = get_test_template_bits(request)
            result = six.text_type(render_placeholder(ctx, "test", layout, "test"))
            # Look for evidence of editing:
            assert "xt-ph-edit" in result
            assert "data-xt-placeholder-name" in result
            assert "data-xt-row" in result
            assert "data-xt-cell" in result


def test_view_config_caches_into_context(rf):
    # This is a silly test...
    request = get_request(edit=False)
    with override_current_theme_class(None):
        (template, layout, gibberish, ctx) = get_test_template_bits(request)
        cfg1 = get_view_config(ctx)
        cfg2 = get_view_config(ctx)
        assert cfg1 is cfg2
        (template, layout, gibberish, ctx) = get_test_template_bits(request, False)
        cfg1 = get_view_config(ctx)
        cfg2 = get_view_config(ctx)
        assert cfg1 is cfg2


def test_missing_plugin_render():
    plugin_id = printable_gibberish()
    cell = LayoutCell(FauxTheme, plugin_identifier=plugin_id)
    assert not cell.plugin_class
    assert not cell.instantiate_plugin()
    assert ("%s?" % plugin_id) in cell.render(None)  # Should render a "whut?" comment


def test_null_cell_render():
    cell = LayoutCell(FauxTheme, None)
    assert not cell.plugin_class
    assert not cell.instantiate_plugin()
    assert not cell.render(None)  # Should render nothing whatsoever!


def test_plugin_naming():
    with plugin_override():
        cell = LayoutCell(FauxTheme, TextPlugin.identifier)
        assert cell.plugin_name == TextPlugin.name


def test_layout_api():
    l = Layout(FauxTheme, "test")
    l.begin_column({"md": 8})
    px0y0 = l.add_plugin("text", {"text": "yes"})
    l.begin_column({"md": 4})
    px1y0 = l.add_plugin("text", {"text": "no"})
    assert len(l) == 1
    assert len(l.rows[0]) == 2
    assert not l.delete_cell(x=0, y=1)  # nonexistent row
    assert l.get_cell(0, 0) == px0y0
    assert l.get_cell(1, 0) == px1y0
    assert not l.get_cell(2, 0)
    assert not l.get_cell(0, 1)
    l.begin_row()
    assert len(l) == 2
    assert len(l.rows[1]) == 0
    l.begin_column()
    assert len(l.rows[1]) == 1
    assert l.delete_cell(x=0, y=1)  # existent cell
    assert not l.delete_cell(x=0, y=1)  # cell existent no more
    assert l.delete_row(1)  # existent row
    assert len(l) == 1
    assert not l.delete_row(1)  # nonexistent row
    l.insert_row(0).add_cell()  # insert a cellful row in first place
    assert len(l) == 2 and list(map(len, l.rows)) == [1, 2]
    l.insert_row(1)  # insert an empty row in second place
    assert len(l) == 3 and list(map(len, l.rows)) == [1, 0, 2]
    assert not l.insert_row(-1)  # that's silly!
    assert l.move_row_to_index(0, 1)
    assert len(l) == 3 and list(map(len, l.rows)) == [0, 1, 2]
    assert l.move_row_to_index(2, 0)
    assert len(l) == 3 and list(map(len, l.rows)) == [2, 0, 1]
    assert not l.move_row_to_index(1, 100)
    assert len(l) == 3 and list(map(len, l.rows)) == [2, 0, 1]
    assert not l.move_row_to_index(1, -1)
    assert len(l) == 3 and list(map(len, l.rows)) == [2, 0, 1]
    cell = l.get_cell(0, 0)
    # top left to bottom right
    assert l.move_cell_to_position(0, 0, 1, 2)
    assert l.get_cell(1, 2) == cell
    assert len(l) == 3 and list(map(len, l.rows)) == [1, 0, 2]
    cell = l.get_cell(0, 0)
    # top left to middle
    assert l.move_cell_to_position(0, 0, 0, 1)
    assert l.get_cell(0, 0) == cell
    assert len(l) == 2 and list(map(len, l.rows)) == [1, 2]
    # invalid cell
    assert not l.move_cell_to_position(0, 100, 0, 1)
    # move to invalid cell
    assert not l.move_cell_to_position(0, 0, 100, 1)


def test_render_custom_size_cell(rf):
    request = get_request(edit=False)
    with override_current_theme_class(None):
        with plugin_override():
            with layout_override():
                layout = Layout(FauxTheme, "test")
                gibberish = printable_gibberish()
                layout.begin_column({"md": None, "xs": None, "sm": None})
                layout.add_plugin("text", {"text": "<p>%s</p>" % gibberish})
                jeng = get_jinja2_engine()
                template = jeng.from_string("")
                template.template.name = "test"
                vars = {"view": FauxView(), "request": request}
                ctx = template.template.new_context(vars)

                result = six.text_type(render_placeholder(ctx, "test", layout, "test"))
                expect = (
                    """
                <div class="placeholder-edit-wrap">
                <div class="xt-ph" id="xt-ph-test">
                <div class="row xt-ph-row">
                <div class="xt-ph-cell"><p>%s</p></div>
                </div>
                </div>
                </div>
                """
                    % gibberish
                )
                assert close_enough(result, expect)
