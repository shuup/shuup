# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest

from shuup.utils.django_compat import reverse
from django.utils.translation import activate

from shuup.core import cache
from shuup.core.models import (
    Category, CategoryStatus, Manufacturer, Product, ProductMode,
    ProductVariationVariable, ProductVariationVariableValue, ShopProduct
)
from shuup.front.utils.sorts_and_filters import (
    set_configuration
)
from shuup.testing.browser_utils import (
    click_element, move_to_element, wait_until_condition,
    wait_until_disappeared
)
from shuup.testing.factories import (
    create_product, get_default_category, get_default_shop,
    get_default_supplier
)
from shuup.testing.browser_utils import initialize_front_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


PRODUCT_DATA = [
    ("Test Product", "sku-1", 123),
    ("A Test Product", "sku-2", 720),
    ("XTest Product", "sku-3", 1),
    ("Test", "sku-4", 42),
    ("Product", "sku-5", 434),
    ("Xtest", "sku-6", 3),
    ("A", "sku-7", 99),
    ("xtest", "sku-8", 999),
    ("a", "sku-9", 42),
    ("test", "sku-10", 53),
    ("product", "sku-11", 34),
]


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@pytest.mark.browser
@pytest.mark.djangodb
def test_search_product_list(browser, live_server, settings):
    activate("en")
    # initialize
    cache.clear()
    shop = get_default_shop()

    for name, sku, price in PRODUCT_DATA:
        create_orderable_product(name, sku, price=price)

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)
    # check that front page actually loaded
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    url = reverse("shuup:product_search")
    browser.visit("%s%s?q=test product" % (live_server, url))

    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 9)

    check_default_ordering(browser)
    # basic_sorting_test(browser)
    second_test_query(browser, live_server, url)


def check_default_ordering(browser):
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="sku-1").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    expected_second_prod_id = "product-%s" % Product.objects.filter(sku="sku-3").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card")[1]["id"] == expected_second_prod_id)

    expected_third_prod_id = "product-%s" % Product.objects.filter(sku="sku-2").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card")[2]["id"] == expected_third_prod_id)


def basic_sorting_test(browser):
    # Sort from Z to A
    click_element(browser, "button[data-id='id_sort']")
    # WARNING: data-original-index was removed after bootstrap-select 1.6.3
    click_element(browser, "li[data-original-index='1'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="sku-3").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Sort by price (highest first)
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='3'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="sku-8").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)


    # Sort by price (lowest first)
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='2'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="sku-3").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Sort from A to Z
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='0'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="sku-2").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)


def second_test_query(browser, live_server, url):
    browser.visit("%s%s?q=Test" % (live_server, url))
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 7)
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="sku-4").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    expected_second_prod_id = "product-%s" % Product.objects.filter(sku="sku-10").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card")[1]["id"] == expected_second_prod_id)

    expected_third_prod_id = "product-%s" % Product.objects.filter(sku="sku-8").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card")[2]["id"] == expected_third_prod_id)

    expected_last_prod_id = "product-%s" % Product.objects.filter(sku="sku-2").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").last["id"] == expected_last_prod_id)
