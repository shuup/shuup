# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.xtheme import Plugin
from shuup.xtheme.resources import (
    RESOURCE_CONTAINER_VAR_NAME,
    InlineMarkupResource,
    InlineScriptResource,
    JinjaMarkupResource,
    ResourceContainer,
    add_resource,
    inject_resources,
)
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.xtheme.utils import get_jinja2_engine, get_request, get_test_template_bits, plugin_override


class ResourceInjectorPlugin(Plugin):
    identifier = "inject"
    message = "I've injected some resources into this page."
    meta_markup = '<meta data-meta="so meta">'
    editor_form_class = None  # Explicitly no form class here :)

    def render(self, context):
        add_resource(context, "body_start", "://example.com/js.js")
        add_resource(context, "body_start", "://foo/fuzz.png")
        add_resource(context, "head_end", "://example.com/css.css")
        add_resource(context, "body_end", InlineScriptResource("alert('xss')"))
        add_resource(context, "head_end", InlineScriptResource.from_vars("foos", {"bars": (1, 2, 3)}))
        add_resource(context, "head_end", InlineMarkupResource(self.meta_markup))
        add_resource(context, "head_end", InlineMarkupResource(self.meta_markup))  # Test duplicates
        add_resource(context, "head_end", "")  # Test the no-op branch
        add_resource(context, "content_start", InlineMarkupResource("START"))
        add_resource(context, "content_end", InlineMarkupResource("END"))
        add_resource(context, "content_end", InlineMarkupResource("END"))
        add_resource(context, "body_end", JinjaMarkupResource("1+1={{ 1+1 }}", context))
        return self.message


def test_injecting_into_weird_places():
    request = get_request()
    (template, layout, gibberish, ctx) = get_test_template_bits(
        request, **{RESOURCE_CONTAINER_VAR_NAME: ResourceContainer()}
    )
    with pytest.raises(ValueError):
        add_resource(ctx, "yes", "hello.js")


def test_without_rc():
    request = get_request()
    (template, layout, gibberish, ctx) = get_test_template_bits(request)
    assert not add_resource(ctx, "yes", "hello.js")
    content1 = "<html>"
    content2 = inject_resources(ctx, content1)
    assert content1 == content2


def test_jinja_resource():
    request = get_request()
    (template, layout, gibberish, context) = get_test_template_bits(request)
    assert JinjaMarkupResource("1+1={{ 1+1|float }}", context).render() == "1+1=2.0"
    assert JinjaMarkupResource("{{ 1|thisdoesnwork }}", context) == "(Error while rendering.)"
    assert JinjaMarkupResource("", context) == ""
    assert str(JinjaMarkupResource("1+1", context)) == "1+1"

    container = ResourceContainer()
    container.add_resource("body_end", JinjaMarkupResource("1+1={{ 1+1|float }}", context))
    container.add_resource("body_end", JinjaMarkupResource("{{ 1|thisdoesnwork }}", context))
    container.add_resource("body_end", JinjaMarkupResource("", context))
    rendered_resource = container._render_resource("://example.com/js.js?random_text")
    assert "unknown resource type" not in rendered_resource
    assert rendered_resource == '<script src="://example.com/js.js?random_text"></script>'
    assert container.render_resources("body_end") == "1+1=2.0(Error while rendering.)"
