# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
from django.utils.translation import activate

from shuup.core import cache
from shuup.core.models import (
    Category,
    CategoryStatus,
    Manufacturer,
    Product,
    ProductMode,
    ProductVariationVariable,
    ProductVariationVariableValue,
    ShopProduct,
    ShopProductVisibility,
)
from shuup.front.utils.sorts_and_filters import set_configuration
from shuup.testing.browser_utils import click_element, initialize_front_browser_test, wait_until_condition
from shuup.testing.factories import create_product, get_default_shop, get_default_supplier
from shuup.utils.django_compat import reverse

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


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_category_product_filters_1(browser, live_server, settings, reindex_catalog):
    cache.clear()  # Avoid cache from past tests
    shop, first_cat, second_cat, third_cat, first_manufacturer = initialize_db()
    reindex_catalog()

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # check that front page actually loaded
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    url = reverse("shuup:category", kwargs={"pk": first_cat.pk, "slug": first_cat.slug})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("First Category"))
    wait_until_condition(browser, lambda x: x.is_text_present("Sort"))
    assert not browser.is_text_present("Manufacturers")  # Since not in default configuration
    hide_sorts_for_shop(browser, shop)
    show_sorts_for_the_category_only(browser, first_cat)
    second_category_page_change(browser, live_server, shop, second_cat)


@pytest.mark.django_db
def test_category_product_filters_2(browser, live_server, settings, reindex_catalog):
    cache.clear()  # Avoid cache from past tests
    shop, first_cat, second_cat, third_cat, first_manufacturer = initialize_db()

    # Activate limit page size changer for the shop
    set_configuration(
        shop=shop,
        data={
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "limit_product_list_page_size": True,
        },
    )
    reindex_catalog()

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # check that front page actually loaded
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    url = reverse("shuup:category", kwargs={"pk": first_cat.pk, "slug": first_cat.slug})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("First Category"))
    wait_until_condition(browser, lambda x: x.is_text_present("Sort"))
    assert not browser.is_text_present("Manufacturers")  # Since not in default configuration
    second_category_sort_test(browser, live_server, shop, second_cat)
    second_category_sort_with_price_filter(browser, second_cat)


@pytest.mark.django_db
def test_category_product_filters_3(browser, live_server, settings, reindex_catalog):
    cache.clear()  # Avoid cache from past tests
    shop, first_cat, second_cat, third_cat, first_manufacturer = initialize_db()
    reindex_catalog()

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # check that front page actually loaded
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    url = reverse("shuup:category", kwargs={"pk": first_cat.pk, "slug": first_cat.slug})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("First Category"))
    wait_until_condition(browser, lambda x: x.is_text_present("Sort"))
    assert not browser.is_text_present("Manufacturers")  # Since not in default configuration
    hide_sorts_for_shop(browser, shop)
    show_sorts_for_the_category_only(browser, first_cat)

    # All sorts for first_cat is available test sorting
    sort_category_products_test(browser, first_cat)

    manufacturer_filter_test(browser, first_cat, first_manufacturer)
    variations_filter_test(browser, first_cat)
    categories_filter_test(browser, first_cat, second_cat, third_cat)


@pytest.mark.django_db
def test_category_product_filters_4(browser, live_server, settings, reindex_catalog):
    """
    Do not show manufacturer option if there is any product
    """
    cache.clear()  # Avoid cache from past tests
    shop, first_cat, second_cat, third_cat, first_manufacturer = initialize_db()

    # remove manufacturers from all products
    Product.objects.all().update(manufacturer=None)
    # show manufacturer filter
    set_configuration(
        category=first_cat,
        data={
            "override_default_configuration": True,
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "filter_products_by_manufacturer": True,
        },
    )
    reindex_catalog()

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # check that front page actually loaded
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    url = reverse("shuup:category", kwargs={"pk": first_cat.pk, "slug": first_cat.slug})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("First Category"))
    wait_until_condition(browser, lambda x: x.is_text_present("Sort"))
    assert not browser.is_text_present("Manufacturers")  # Since there is no product with manufacturer

    # add the manufacturer to the last product so the manufacturer filter is show
    last_product = Product.objects.last()
    last_product.manufacturer = first_manufacturer
    last_product.save()
    reindex_catalog()
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_text_present("Manufacturers")

    # set the shop product hidden
    shop_product = last_product.get_shop_instance(shop)
    shop_product.visibility = ShopProductVisibility.NOT_VISIBLE
    shop_product.save()
    reindex_catalog()

    # the manufacturer filter is removed
    browser.visit("%s%s" % (live_server, url))
    assert not browser.is_text_present("Manufacturers")


def initialize_db():
    activate("en")
    # initialize
    cache.clear()
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    supplier.stock_managed = False
    supplier.save()

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

    # Add some variation products
    add_variations(shop, Product.objects.filter(sku="test-sku-1").first(), ["Black", "Yellow"], ["Big", "Small"])

    add_variations(shop, Product.objects.filter(sku="test-sku-2").first(), ["Brown", "Pink"], ["S", "L", "XL"])

    add_variations(shop, Product.objects.filter(sku="test-sku-3").first(), ["Brown", "Black"], ["S", "L", "XL", "Big"])

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

    return shop, first_cat, second_cat, third_cat, first_manufacturer


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


def hide_sorts_for_shop(browser, shop):
    set_configuration(shop=shop, data={"sort_products_by_name": False, "sort_products_by_price": False})
    browser.reload()
    wait_until_condition(browser, lambda x: not x.is_text_present("sort"), timeout=20)


def show_sorts_for_the_category_only(browser, category):
    set_configuration(category=category, data={"override_default_configuration": True, "sort_products_by_name": True})
    browser.reload()
    wait_until_condition(browser, lambda x: x.is_text_present("Sort"))
    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_sort option")) == 2)
    click_element(browser, "button[data-id='id_sort']")

    set_configuration(
        category=category,
        data={
            "override_default_configuration": True,
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "sort_products_by_date_created": True,
            "sort_products_by_date_created_ordering": 3,
        },
    )
    browser.reload()
    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_sort option")) == 5)


def sort_category_products_test(browser, category):
    # Lowest price first
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "button[data-id='id_sort'] + .dropdown-menu li:nth-child(3) a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-3").first().id
    wait_until_condition(browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Name from A-Z
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "button[data-id='id_sort'] + .dropdown-menu li:nth-child(1) a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-2").first().id
    wait_until_condition(browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Name from Z-A
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "button[data-id='id_sort'] + .dropdown-menu li:nth-child(2) a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-3").first().id
    wait_until_condition(browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Highest price first
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "button[data-id='id_sort'] + .dropdown-menu li:nth-child(4) a")
    expected_first_prod_id = "product-%s" % Product.objects.filter(sku="test-sku-2").first().id
    wait_until_condition(browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)

    # Date created
    click_element(browser, "button[data-id='id_sort']")
    click_element(browser, "button[data-id='id_sort'] + .dropdown-menu li:nth-child(5) a")
    expected_first_prod_id = (
        "product-%s"
        % Product.objects.filter(shop_products__primary_category=category).order_by("-created_on").first().id
    )
    wait_until_condition(browser, lambda x: x.find_by_css(".product-card").first["id"] == expected_first_prod_id)


def manufacturer_filter_test(browser, category, manufacturer):
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 3)
    set_configuration(
        category=category,
        data={
            "override_default_configuration": True,
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "filter_products_by_manufacturer": True,
        },
    )
    browser.reload()
    wait_until_condition(browser, lambda x: x.is_text_present("Manufacturers"))
    browser.execute_script("$('#manufacturers-%s').click();" % manufacturer.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)


def variations_filter_test(browser, category):
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)
    # Activate categories filter for current category which is the first one
    set_configuration(
        category=category,
        data={
            "override_default_configuration": True,
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "filter_products_by_variation_value": True,
            "filter_products_by_variation_value_ordering": 1,
        },
    )

    def get_var_id(value):
        return value.replace(" ", "*")

    browser.reload()
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 3)

    # Two brown products
    browser.execute_script("$('#variation_color-%s').click();" % get_var_id("Brown"))
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 2)

    # Two brown L sized products
    browser.execute_script("$('#variation_size-%s').click();" % get_var_id("L"))
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 2)

    # One brown big
    browser.execute_script("$('#variation_size-%s').click();" % get_var_id("Big"))
    browser.execute_script("$('#variation_size-%s').click();" % get_var_id("L"))
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)

    browser.execute_script("$('#variation_color-%s').click();" % get_var_id("Brown"))  # unselect brown

    # Two Big or Black products
    browser.execute_script("$('#variation_color-%s').click();" % get_var_id("Black"))

    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 2)

    browser.execute_script("$('#variation_color-%s').click();" % get_var_id("Black"))  # unselect black

    # Three Big or Pink products
    browser.execute_script("$('#variation_color-%s').click();" % get_var_id("Pink"))
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 0)

    # One pink product
    browser.execute_script("$('#variation_size-%s').click();" % get_var_id("Big"))
    browser.execute_script("$('#variation_size-%s').click();" % get_var_id("Brown"))
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
            "override_default_configuration": True,
            "sort_products_by_name": True,
            "sort_products_by_name_ordering": 1,
            "sort_products_by_price": True,
            "sort_products_by_price_ordering": 2,
            "filter_products_by_category": True,
        },
    )
    browser.reload()
    wait_until_condition(browser, lambda x: x.is_element_present_by_id("categories-%s" % third_cat.id))
    browser.execute_script("$('#categories-%s').click();" % third_cat.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)
    browser.execute_script("$('#categories-%s').click();" % second_cat.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1)
    browser.execute_script("$('#categories-%s').click();" % third_cat.id)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 12)


def second_category_page_change(browser, live_server, shop, category):
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    browser.visit("%s%s" % (live_server, url))
    assert not browser.is_text_present("Sort")  # Sort shouldn't be available since default configurations
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 12)
    click_element(browser, "#next_page a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 1, timeout=30)
    click_element(browser, "#previous_page a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 12, timeout=30)


def second_category_sort_test(browser, live_server, shop, category):
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    browser.visit("%s%s" % (live_server, url))

    wait_until_condition(browser, lambda x: x.is_element_present_by_css("button[data-id='id_limit']"), timeout=30)
    # Set limit to 24
    click_element(browser, "button[data-id='id_limit']")
    click_element(browser, "button[data-id='id_limit'] + .dropdown-menu li:nth-child(2) a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 13, timeout=30)

    # Check that visibility change affects the product count
    shop_products = ShopProduct.objects.filter(primary_category_id=category.id)[:3]
    for sp in shop_products:
        sp.visibility = ShopProductVisibility.NOT_VISIBLE
        sp.save()

    cache.clear()
    browser.reload()
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 10)

    for sp in shop_products:
        sp.visibility = ShopProductVisibility.ALWAYS_VISIBLE
        sp.save()

    cache.clear()
    browser.reload()
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 13, timeout=30)


def add_variations(shop, parent, colors, sizes):
    supplier = get_default_supplier()
    color_var = ProductVariationVariable.objects.create(product_id=parent.id, identifier="color", name="Color")
    size_var = ProductVariationVariable.objects.create(product_id=parent.id, identifier="size", name="Size")

    for color in colors:
        ProductVariationVariableValue.objects.create(variable_id=color_var.id, value=color)
    for size in sizes:
        ProductVariationVariableValue.objects.create(variable_id=size_var.id, value=size)

    combinations = list(parent.get_all_available_combinations())
    assert len(combinations) == (len(sizes) * len(colors))
    for combo in combinations:
        assert not combo["result_product_pk"]
        child = create_product(sku="%s-xyz-%s" % (parent.sku, combo["sku_part"]), shop=shop, supplier=supplier)
        child.link_to_parent(parent, combination_hash=combo["hash"])
    assert parent.mode == ProductMode.VARIABLE_VARIATION_PARENT


def second_category_sort_with_price_filter(browser, category):
    set_configuration(
        category=category,
        data={
            "override_default_configuration": True,
            "filter_products_by_price": True,
            "filter_products_by_price_range_min": 5,
            "filter_products_by_price_range_max": 12,
            "filter_products_by_price_range_size": 3,
        },
    )
    browser.reload()

    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_price_range option")) == 5)

    # let's filter all products with price less than 5 => 5
    click_element(browser, "button[data-id='id_price_range']")
    click_element(browser, "button[data-id='id_price_range'] + .dropdown-menu li:nth-child(2) a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 5)

    # let's filter products with price +12 => 2
    click_element(browser, "button[data-id='id_price_range']")
    click_element(browser, "button[data-id='id_price_range'] + .dropdown-menu li:nth-child(5) a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 2)

    # filter with price 8-11 => 4
    click_element(browser, "button[data-id='id_price_range']")
    click_element(browser, "button[data-id='id_price_range'] + .dropdown-menu li:nth-child(4) a")
    wait_until_condition(browser, lambda x: len(x.find_by_css(".product-card")) == 4)
