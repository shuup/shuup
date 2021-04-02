# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
import time

from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    move_to_element,
    wait_until_appeared,
    wait_until_appeared_xpath,
    wait_until_condition,
)
from shuup.testing.factories import create_product, create_random_person, get_default_shop, get_default_supplier
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def create_contacts(shop):
    for i in range(0, 200):
        contact = create_random_person()
        contact.save()


def create_products(shop):
    supplier = get_default_supplier()
    for i in range(0, 200):
        sku = "sku-%d" % i
        create_product(sku, shop, supplier, default_price=i)


# used in settings
list_view_settings = {
    "contact": {
        "page_header": "Contacts",
        "default_column_count": 7,
        "addable_fields": [(1, "Account Manager")],
        "creator": create_contacts,
        "test_pagination": True,
    },
    "shop_product": {
        "page_header": "Shop Products",
        "default_column_count": 7,
        "addable_fields": [(22, "Product Gtin"), (3, "Default Price")],
        "creator": create_products,
        "test_pagination": False,
    },
    "permission_group": {
        "page_header": "Permission Groups",
        "default_column_count": 1,
        "addable_fields": [(2, "Permissions"), (1, "Id")],  # use reverse order due idx
        "creator": None,
        "test_pagination": False,
    },
}


@pytest.mark.django_db
@pytest.mark.parametrize("visit_type", list_view_settings.keys())
def test_list_views(browser, admin_user, live_server, settings, visit_type):
    shop = get_default_shop()
    creator = list_view_settings[visit_type].get("creator", None)

    if creator and callable(creator):
        creator(shop)

    initialize_admin_browser_test(browser, live_server, settings)
    _visit_list_view(browser, live_server, visit_type, creator)
    if list_view_settings[visit_type].get("test_pagination", False):
        _test_pagination(browser)
    _set_settings(browser, visit_type, creator)


def _visit_list_view(browser, live_server, list_view_name, creator):
    url = reverse("shuup_admin:%s.list" % list_view_name)
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present(list_view_settings[list_view_name]["page_header"]))
    _check_picotable_item_info(browser, creator)


def _test_pagination(browser):
    ellipses = u"\u22ef"

    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", "2", "3", ellipses, "10", "Next"])

    _goto_page(browser, 3)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", "2", "3", "4", "5", ellipses, "10", "Next"])

    _goto_page(browser, 5)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "3", "4", "5", "6", "7", ellipses, "10", "Next"])

    _goto_page(browser, 7)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "5", "6", "7", "8", "9", "10", "Next"])

    _goto_page(browser, 9)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "7", "8", "9", "10", "Next"])

    _goto_page(browser, 10)
    items = _get_pagination_content(browser)
    _assert_pagination_content(items, ["Previous", "1", ellipses, "8", "9", "10", "Next"])


def _get_pagination_content(browser):
    pagination = browser.find_by_css(".pagination")[0]
    return pagination.find_by_tag("a")


def _assert_pagination_content(items, content):
    assert [item.text for item in items] == content


def _goto_page(browser, page_number):
    click_element(browser, "a[rel='%s']" % page_number)
    element = "li.active a[rel='%s']" % page_number
    wait_until_appeared(browser, element)
    move_to_element(browser, element)


def _click_item(items, value):
    index = [item.text for item in items].index(value)
    items[index].click()
    time.sleep(0.5)  # Wait mithril for a half sec


def _set_settings(browser, setting_type, creator):
    used_settings = list_view_settings[setting_type]
    default_column_count = used_settings["default_column_count"]
    addable_fields = used_settings["addable_fields"]

    # not selected by default
    for idx, text in addable_fields:
        assert not browser.is_text_present(text)

    click_element(browser, ".shuup-toolbar .btn.btn-inverse")

    # select settings
    for idx, (index_key, text) in enumerate(addable_fields):
        expected_index = default_column_count + 1 + idx
        assert browser.is_text_present(text)
        browser.find_by_xpath("//ul[@id='source-sortable']/li[%d]/button" % index_key).first.click()
        wait_until_appeared_xpath(browser, "//ul[@id='target-sortable']/li[%d]/button" % expected_index)

    # save settings
    # scroll to top
    move_to_element(browser, ".shuup-toolbar .btn.btn-success")
    browser.find_by_css(".shuup-toolbar .btn.btn-success").first.click()
    _check_picotable_item_info(browser, creator)

    if creator:
        for idx, text in addable_fields:
            wait_until_condition(browser, lambda x: x.is_text_present(text))

    # go back to settings
    click_element(browser, ".shuup-toolbar .btn.btn-inverse")

    wait_until_appeared_xpath(browser, "//a[contains(text(),'Reset Defaults')]")

    # reset to defaults
    browser.find_by_xpath("//a[contains(text(),'Reset Defaults')]").click()

    _check_picotable_item_info(browser, creator)

    # not selected by default
    if creator:
        for idx, text in addable_fields:
            assert not browser.is_text_present(text)


def _check_picotable_item_info(browser, creator):
    time.sleep(1)
    if creator:
        move_to_element(browser, ".picotable-item-info")
        wait_until_appeared(browser, ".picotable-item-info")
    else:
        wait_until_condition(
            browser, condition=lambda x: x.is_text_present("There are no granular permission groups to show")
        )
