# -*- coding: utf-8 -*-
import pytest

from shoop.xtheme.plugins import Plugin
from shoop.xtheme.resources import (
    RESOURCE_CONTAINER_VAR_NAME, InlineMarkupResource, InlineScriptResource, ResourceContainer, add_resource,
    inject_resources
)
from shoop.xtheme.theme import override_current_theme_class
from shoop_tests.xtheme.utils import get_jinja2_engine, get_request, get_test_template_bits, plugin_override


class ResourceInjectorPlugin(Plugin):
    identifier = "inject"
    message = "I've injected some resources into this page."
    meta_markup = "<meta data-meta=\"so meta\">"

    def render(self, context):
        add_resource(context, "body_start", "://example.com/js.js")
        add_resource(context, "body_start", "://foo/fuzz.png")
        add_resource(context, "head_end", "://example.com/css.css")
        add_resource(context, "body_end", InlineScriptResource("alert('xss')"))
        add_resource(context, "head_end", InlineScriptResource.from_vars("foos", {"bars": (1, 2, 3)}))
        add_resource(context, "head_end", InlineMarkupResource(self.meta_markup))
        add_resource(context, "head_end", InlineMarkupResource(self.meta_markup))  # Test duplicates
        add_resource(context, "head_end", "")  # Test the no-op branch
        return self.message


def test_resources():
    request = get_request(edit=False)
    with override_current_theme_class(None):
        with plugin_override():
            jeng = get_jinja2_engine()
            template = jeng.get_template("resinject.jinja")
            output = template.render(request=request)
            head, body = output.split("</head>", 1)
            assert "alert('xss')" in body  # the inline script
            assert '"bars": [1, 2, 3]' in head  # the script vars
            assert '(unknown resource type:' in body  # the png
            assert 'href="://example.com/css.css"' in head  # the css
            assert 'src="://example.com/js.js"' in body  # the js
            assert head.count(ResourceInjectorPlugin.meta_markup) == 1  # the duplicate meta
            assert ResourceInjectorPlugin.message in output  # the actual message


def test_injecting_into_weird_places():
    request = get_request()
    (template, layout, gibberish, ctx) = get_test_template_bits(request, **{
        RESOURCE_CONTAINER_VAR_NAME: ResourceContainer()
    })
    with pytest.raises(ValueError):
        add_resource(ctx, "yes", "hello.js")


def test_without_rc():
    request = get_request()
    (template, layout, gibberish, ctx) = get_test_template_bits(request)
    assert not add_resource(ctx, "yes", "hello.js")
    content1 = "<html>"
    content2 = inject_resources(ctx, content1)
    assert content1 == content2
