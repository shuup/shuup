# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
from django.test import override_settings

from shuup.core import cache
from shuup.testing import factories
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.utils.django_compat import reverse
from shuup.xtheme import get_current_theme
from shuup.xtheme.models import Snippet

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_snippet_injection(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    initialize_admin_browser_test(browser, live_server, settings)

    url = reverse("shuup_admin:xtheme_snippet.new")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("New Snippet"))
    browser.execute_script("$(\"[name='location']\").val('body_end').trigger('change')")
    browser.execute_script("$(\"[name='snippet_type']\").val('inline_js').trigger('change')")
    browser.execute_script(
        "window.ShuupCodeMirror.editors[document.getElementById('id_snippet-snippet')].setValue('alert(\"works\")');"
    )
    click_element(browser, "button[type='submit']")
    wait_until_appeared(browser, "div[class='message success']")

    url = reverse("shuup:index")
    browser.visit("%s%s" % (live_server, url))

    def has_alert(browser):
        try:
            return browser.get_alert().text == "works"
        except:
            return False

    wait_until_condition(browser, has_alert)
    browser.get_alert().accept()

    theme = get_current_theme(shop)
    snippet = Snippet.objects.filter(shop=shop).first()
    snippet.themes = [theme.identifier]
    snippet.save()

    cache.clear()
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, has_alert)
    browser.get_alert().accept()

    snippet.themes = ["doesnt-exist"]
    snippet.save()

    cache.clear()
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    with pytest.raises(Exception):
        browser.get_alert()

    # delete the snippet
    url = reverse("shuup_admin:xtheme_snippet.edit", kwargs=dict(pk=snippet.pk))
    browser.visit("%s%s" % (live_server, url))
    assert Snippet.objects.filter(shop=shop).exists()

    click_element(browser, ".shuup-toolbar button.btn.btn-danger")
    browser.get_alert().accept()
    wait_until_condition(browser, lambda x: not Snippet.objects.filter(shop=shop).exists())
