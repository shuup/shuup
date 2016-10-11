# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest

from django.core.urlresolvers import reverse

from shuup.core import cache
from shuup.core.models import (
    Category, CategoryStatus, Manufacturer, Product, ShopProduct
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
from shuup.testing.utils import initialize_front_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


CATEGORY_DATA = [
    ("First Category", "cat-1"),
    ("Second Category", "cat-2"),
    ("Third Category", "cat-3"),
]


MANUFACTURER_DATA = [
    ("First Manufacturer", "man-1"),
    ("Second Manufacturer", "man-2"),
]

FIRST_CATEGORY_PRODUCT_DATA = [
    ("Test Product", "test-sku-1", 123),
    ("A Test Product", "test-sku-2", 720),
    ("XTest Product", "test-sku-3", 1),
]


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@pytest.mark.browser
@pytest.mark.djangodb
def test_category_product_list(browser, live_server, settings):
    # initialize
    cache.clear()
    shop = get_default_shop()
    
    for name, identifier in CATEGORY_DATA:
        category = Category()
        category.name = name
        category.identifier = identifier
        category.status = CategoryStatus.VISIBLE
        category.save()
        category.shops.add(shop)

    for name, identifier in MANUFACTURER_DATA:
        Manufacturer.objects.create(name=name, identifier=identifier)

    first_cat = Category.objects.filter(identifier="cat-1").first()
    second_cat = Category.objects.filter(identifier="cat-2").first()
    third_cat = Category.objects.filter(identifier="cat-3").first()
    assert first_cat.pk != second_cat.pk
    for name, sku, price in FIRST_CATEGORY_PRODUCT_DATA:
        product = create_orderable_product(name, sku, price=price)
        shop_product = product.get_shop_instance(shop)
        cat = Category.objects.first()
        shop_product.primary_category = first_cat
        shop_product.save()
        shop_product.categories.add(first_cat)

    for i in range(1, 14):
        product = create_orderable_product("Test product", "sku-%s" % i, price=i)
        shop_product = product.get_shop_instance(shop)
        cat = Category.objects.first()
        shop_product.primary_category = second_cat
        shop_product.save()
        shop_product.categories.add(second_cat)


    # Set manufacturer for first product only
    first_manufacturer = Manufacturer.objects.first()
    Product.objects.filter(sku="test-sku-1").update(manufacturer_id=first_manufacturer.id)

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # check that front page actually loaded
    assert browser.is_text_present("Welcome to Default!")

    url = reverse("shuup:category", kwargs={"pk": first_cat.pk, "slug": first_cat.slug})
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_text_present("First Category")
    assert browser.is_text_present("Sort")
    assert not browser.is_text_present("Manufacturers")  # Since not in default configuration
    hide_sorts_for_shop(browser, shop)
    show_sorts_for_the_category_only(browser, first_cat)

    # All sorts for first_cat is available test sorting
    sort_category_products_test(browser, first_cat)

    manufacturer_filter_test(browser, first_cat, first_manufacturer)
    categories_filter_test(browser, first_cat, second_cat, third_cat)

    second_category_sort_test(browser, live_server, shop, second_cat)


def hide_sorts_for_shop(browser, shop):
    set_configuration(
        shop=shop, data={"sort_products_by_name": False, "sort_products_by_price": False})
    browser.reload()
    assert not browser.is_text_present("Sort")


def show_sorts_for_the_category_only(browser, category):
    set_configuration(category=category, data={"sort_products_by_name": True})
    browser.reload()
    assert browser.is_text_present("Sort")
    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_sort option")) == 2)
    click_element(browser, "button[data-id='id_sort']")

    set_configuration(
        category=category,
        data={
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "sort_products_by_date_created": True,
            "sort_products_by_date_created_ordering": 3
        }
    )
    browser.reload()
    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_sort option")) == 5)
    

def sort_category_products_test(browser, category):
    # Lowest price first
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='2'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-3").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Name from A-Z
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='0'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-2").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Name from Z-A
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='1'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-3").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)


    # Highest price first
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='3'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-2").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Date created
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "li[data-original-index='4'] a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(
        shop_products__primary_category=category).order_by("-created_on").first().id
    wait_until_condition(
        browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)


def manufacturer_filter_test(browser, category, manufacturer):
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 3)
    set_configuration(
        category=category,
        data={
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "filter_products_by_manufacturer": True
        }
    )
    browser.reload()
    assert browser.is_text_present("Manufacturers")
    browser.execute_script("$('#manufacturers-%s').click();" % manufacturer.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)


def categories_filter_test(browser, first_cat, second_cat, third_cat):
    # Add all products in second category to also in first category
    for shop_product in ShopProduct.objects.filter(primary_category=second_cat):
        shop_product.categories.add(first_cat)
    # Add one product including first_cat also to third_cat
    shop_product = ShopProduct.objects.filter(primary_category=first_cat).last()
    shop_product.categories.add(third_cat)

    # Activate categories filter for current category which is the first one
    set_configuration(
        category=first_cat,
        data={
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "filter_products_by_category": True
        }
    )
    browser.reload()
    browser.execute_script("$('#categories-%s').click();" % third_cat.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)
    browser.execute_script("$('#categories-%s').click();" % second_cat.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)
    browser.execute_script("$('#categories-%s').click();" % third_cat.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 12)



def second_category_sort_test(browser, live_server, shop, category):
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    browser.visit("%s%s" % (live_server, url))
    assert not browser.is_text_present("Sort")  # Sort shouldn't be available since default configurations
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 12)
    click_element(browser, "#next_page a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1, timeout=30)
    click_element(browser, "#previous_page a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 12, timeout=30)

    # Activate limit page size changer
    set_configuration(
        shop=shop,
        data={
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "limit_product_list_page_size": True
        }
    )
    browser.reload()
    # Set limit to 24
    browser.select("limit", 24)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 13)
