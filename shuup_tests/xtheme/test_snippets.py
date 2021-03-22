# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup

from shuup.apps.provides import override_provides
from shuup.core import cache
from shuup.testing import factories
from shuup.xtheme._theme import get_current_theme
from shuup.xtheme.models import Snippet, SnippetType
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_theme_selection():
    cache.clear()

    shop = factories.get_default_shop()
    theme = get_current_theme(shop)

    test_js_script = 'console.log("this is JS snippet");'
    js_snippet = Snippet.objects.create(
        shop=shop,
        location="body_end",
        snippet_type=SnippetType.InlineJS,
        snippet=test_js_script,
        themes=theme.identifier,
    )

    test_css_style = "h1 { font-size: 3px; }"
    css_snippet = Snippet.objects.create(
        shop=shop,
        location="head_end",
        snippet_type=SnippetType.InlineCSS,
        snippet=test_css_style,
        themes=theme.identifier,
    )

    test_html_code = '<p class="test-snippet">Test HTML snippet</p>'
    html_snippet = Snippet.objects.create(
        shop=shop,
        location="body_end",
        snippet_type=SnippetType.InlineHTMLMarkup,
        snippet=test_html_code,
        themes=theme.identifier,
    )

    test_jinja_code = '<p class="test-snippet">Test Jinja snippet %s</p>'
    jinja_snippet = Snippet.objects.create(
        shop=shop,
        location="body_end",
        snippet_type=SnippetType.InlineJinjaHTMLMarkup,
        snippet=test_jinja_code % ("{{ request.shop.public_name}}"),
    )

    html_that_should_not_exist = "<h1>-Hello world</h1>"
    snippet_for_other_theme = Snippet.objects.create(
        shop=shop,
        location="body_end",
        snippet_type=SnippetType.InlineHTMLMarkup,
        snippet=html_that_should_not_exist,
        themes="random.theme",
    )
    with override_provides("xtheme_resource_injection", ["shuup.xtheme.resources:inject_global_snippet"]):
        client = SmartClient()
        response, soup = client.response_and_soup("/")
        assert response.status_code == 200

        assert html_that_should_not_exist not in str(soup)

        body = str(soup.find("body"))
        assert "<script>%s</script>" % test_js_script in body
        assert test_html_code in body
        assert (test_jinja_code % shop.public_name) in body

        head = str(soup.find("head"))
        assert '<style type="text/css">%s</style>' % test_css_style in head

        # Admin views are not allowed to inject into
        client = SmartClient()
        response, soup = client.response_and_soup("/sa/login/")
        assert response.status_code == 200

        soup_str = str(soup)
        assert html_that_should_not_exist not in soup_str
        assert ('<style type="text/css">%s</style>' % test_css_style) not in soup_str
