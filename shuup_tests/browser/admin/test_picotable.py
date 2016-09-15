# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import time

import pytest
from django.core.urlresolvers import reverse

from shuup.testing.browser_utils import click_element, wait_until_appeared
from shuup.testing.factories import create_random_person, get_default_shop
from shuup.testing.utils import initialize_admin_browser_test


pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_list_view(browser, admin_user, live_server):
    shop = get_default_shop()
    for i in range(0, 200):
        contact = create_random_person()
        contact.save()
    initialize_admin_browser_test(browser, live_server)
    _visit_contacts_list_view(browser, live_server)
    _test_pagination(browser)
    _set_settings(browser)


def _visit_contacts_list_view(browser, live_server):
    url = reverse("shuup_admin:contact.list")
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_text_present("Contacts")
    wait_until_appeared(browser, ".picotable-item-info")


def _test_pagination(browser):
    ellipses = u"\u22ef"

    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", "2", "3", ellipses, "11", "Next"])

    _goto_page(browser, 3)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", "2", "3", "4", "5",  ellipses, "11", "Next"])

    _goto_page(browser, 5)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "3", "4", "5", "6", "7", ellipses, "11", "Next"])


    _goto_page(browser, 7)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "5", "6", "7", "8", "9", ellipses, "11", "Next"])


    _goto_page(browser, 9)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "7", "8", "9", "10", "11", "Next"])


    _goto_page(browser, 11)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "9", "10", "11", "Next"])


def _get_pagination_content(browser):
    pagination = browser.find_by_css(".pagination")[0]
    return pagination.find_by_tag("a")


def _assert_pagination_content(items, content):
    assert [item.text for item in items] == content


def _goto_page(browser, page_number):
    click_element(browser, "a[rel='%s']" % page_number)
    wait_until_appeared(browser, "li.active a[rel='%s']" % page_number)


def _click_item(items, value):
    index = [item.text for item in items].index(value)
    items[index].click()
    time.sleep(0.5)  # Wait mithril for a half sec


def _set_settings(browser):
    assert not browser.is_text_present("Internal Identifier")
    browser.find_by_css(".btn.btn-default.btn-inverse").click()
    browser.find_by_id("id_view_configuration_contact_identifier").click()
    browser.find_by_css(".btn.btn-success").click()
    wait_until_appeared(browser, ".picotable-item-info")
    assert browser.is_text_present("Internal Identifier")

