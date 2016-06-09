# -*- coding: utf-8 -*-
from shuup.xtheme import Plugin, templated_plugin_factory, TemplatedPlugin
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import printable_gibberish
from shuup_tests.xtheme.utils import get_jinja2_engine, plugin_override


def test_plugin_choices():
    with plugin_override():
        choice_identifiers = set(c[0] for c in Plugin.get_plugin_choices())
        assert choice_identifiers == set(("inject", "text"))


def test_templated_plugin():
    jeng = get_jinja2_engine()

    my_plugin_class = templated_plugin_factory("MyPlugin", "templated_plugin.jinja",
        inherited_variables=("name",),
        config_copied_variables=("greeting",),
        engine=jeng
    )
    top_context = {
        "name": printable_gibberish(),
    }
    config = {
        "greeting": "Good day"
    }
    plugin = my_plugin_class(config=config)
    assert isinstance(plugin, TemplatedPlugin)
    with override_current_theme_class(None):
        rendered_content = plugin.render(top_context)
        expected_content = "Good day %s" % top_context["name"]
        assert rendered_content == expected_content
