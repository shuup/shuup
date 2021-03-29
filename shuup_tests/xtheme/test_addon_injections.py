# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings
from mock import MagicMock

from shuup.apps.provides import override_provides
from shuup.core import cache
from shuup.testing.factories import get_default_shop
from shuup.xtheme.models import Snippet, SnippetType
from shuup.xtheme.resources import InlineScriptResource, add_resource
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.xtheme.utils import FauxView, get_jinja2_engine, get_request


def add_test_injection(context, content):
    add_resource(context, "body_end", InlineScriptResource("window.injectedFromAddon=true;"))


@pytest.mark.django_db
def test_simple_addon_injection():
    request = get_request(edit=False)
    request.shop = get_default_shop()
    jeng = get_jinja2_engine()
    template = jeng.get_template("resinject.jinja")

    with override_current_theme_class():
        with override_provides(
            "xtheme_resource_injection",
            [
                "shuup_tests.xtheme.test_addon_injections:add_test_injection",
            ],
        ):
            # TestInjector should add alert to end of the body for every request
            output = template.render(request=request)
            head, body = output.split("</head>", 1)
            assert "window.injectedFromAddon=true;" in body

            with override_settings(SHUUP_XTHEME_EXCLUDE_TEMPLATES_FROM_RESOUCE_INJECTION=["resinject.jinja"]):
                output = template.render(request=request)
                head, body = output.split("</head>", 1)
                assert "window.injectedFromAddon=true;" not in body


@pytest.mark.django_db
def test_global_snippet_resource_injection():
    request = get_request(edit=False)
    request.shop = get_default_shop()
    jeng = get_jinja2_engine()
    template = jeng.get_template("resinject.jinja")
    request.resolver_match = MagicMock(app_name="shuup")
    context = dict(view=FauxView, request=request)

    with override_provides("xtheme_resource_injection", ["shuup.xtheme.resources:inject_global_snippet"]):
        with override_current_theme_class():
            output = template.render(context, request=request)
            assert "<div>1</div>" not in output

            Snippet.objects.create(
                shop=request.shop,
                location="body_end",
                snippet_type=SnippetType.InlineJinjaHTMLMarkup,
                snippet="""
                    {% set x = 1 %}
                    <div>{{- x -}}</div>
                """,
            )

        cache.clear()

        with override_current_theme_class():
            output = template.render(context, request=request)
            assert "<div>1</div>" in output
