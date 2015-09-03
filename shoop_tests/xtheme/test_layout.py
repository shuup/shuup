# -*- coding: utf-8 -*-
from shoop.xtheme.theme import override_current_theme_class
import six

from shoop.xtheme.layout import Layout
from shoop.xtheme.rendering import get_view_config, render_placeholder
from shoop_tests.xtheme.utils import close_enough, get_request, get_test_template_bits, plugin_override


def test_layout_serialization():
    with plugin_override():
        l = Layout("test")
        l.begin_column({"md": 8})
        l.add_plugin("text", {"text": "yes"})
        serialized = l.serialize()
        expected = {
            'name': "test",
            'rows': [
                {
                    'cells': [
                        {'config': {'text': 'yes'}, 'plugin': 'text', 'sizes': {"md": 8}}
                    ]
                }
            ]
        }
        assert serialized == expected
        assert Layout.unserialize(serialized).serialize() == expected


def test_layout_rendering(rf):
    request = get_request(edit=False)
    with override_current_theme_class(None):
        with plugin_override():
            (template, layout, gibberish, ctx) = get_test_template_bits(request)

            result = six.text_type(render_placeholder(ctx, "test", layout, "test"))
            expect = """
            <div class="xt-ph" id="xt-ph-test">
            <div class="row xt-ph-row">
            <div class="col-md-12 hidden-xs xt-ph-cell">%s</div>
            </div>
            </div>
            """ % gibberish
            assert close_enough(result, expect)


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
    (template, layout, gibberish, ctx) = get_test_template_bits(request)
    cfg1 = get_view_config(ctx)
    cfg2 = get_view_config(ctx)
    assert cfg1 is cfg2
    (template, layout, gibberish, ctx) = get_test_template_bits(request, False)
    cfg1 = get_view_config(ctx)
    cfg2 = get_view_config(ctx)
    assert cfg1 is cfg2
