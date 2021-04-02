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
from django.contrib.auth.models import Group, Permission

from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import (
    get_default_model_permissions,
    get_permission_object_from_string,
    set_permissions_for_group,
)
from shuup.core.models import Category, Product, Shop, ShopProduct
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.testing.factories import (
    create_random_user,
    get_default_product_type,
    get_default_sales_unit,
    get_default_shop,
    get_default_tax_class,
)
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
def test_quick_add(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    get_default_product_type()
    get_default_sales_unit()
    get_default_tax_class()
    initialize_admin_browser_test(browser, live_server, settings)

    url = reverse("shuup_admin:shop_product.new")
    browser.visit("%s%s" % (live_server, url))
    sku = "testsku"
    name = "Some product name"
    price_value = 10
    short_description = "short but gold"

    browser.fill("base-sku", sku)
    browser.fill("base-name__en", name)
    browser.fill("base-short_description__en", short_description)
    browser.fill("shop%s-default_price_value" % shop.pk, price_value)

    wait_until_appeared(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    click_element(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    wait_until_appeared(browser, "#create-object-iframe")

    with browser.get_iframe("create-object-iframe") as iframe:
        assert Category.objects.count() == 0
        wait_until_appeared(iframe, "input[name='base-name__en']")
        iframe.fill("base-name__en", "Test Category")
        time.sleep(3)  # Let's just wait here to the iFrame to open fully (for Chrome and headless)
        wait_until_appeared(iframe, "button[form='category_form']")
        click_element(browser, "button[form='category_form']")
        wait_until_condition(browser, condition=lambda x: Category.objects.count() == 1, timeout=20)

    assert Category.objects.first().name == "Test Category"

    # click to edit the button
    click_element(browser, "#id_shop%d-primary_category ~ .edit-object-btn a.btn" % shop.id)

    with browser.get_iframe("create-object-iframe") as iframe:
        wait_until_appeared(iframe, "input[name='base-name__en']")
        new_cat_name = "Changed Name"
        iframe.fill("base-name__en", new_cat_name)
        time.sleep(3)  # Let's just wait here to the iFrame to open fully (for Chrome and headless)
        wait_until_appeared(iframe, "button[form='category_form']")
        click_element(iframe, "button[form='category_form']")

    wait_until_condition(browser, condition=lambda x: Category.objects.first().name == new_cat_name, timeout=20)

    click_element(browser, "button[form='product_form']")
    wait_until_appeared(browser, "div[class='message success']")


@pytest.mark.django_db
def test_edit_button_no_permission(browser, admin_user, live_server, settings):
    shop = get_default_shop()

    manager_group = Group.objects.create(name="Managers")

    manager = create_random_user("en", is_staff=True)
    manager.username = "manager"
    manager.set_password("password")
    manager.save()
    manager.groups.add(manager_group)
    shop.staff_members.add(manager)

    # add permissions for Product admin module
    manager_permissions = set(["dashboard", "Products", "shop_product.new"])
    set_permissions_for_group(manager_group, manager_permissions)

    get_default_product_type()
    get_default_sales_unit()
    get_default_tax_class()
    initialize_admin_browser_test(browser, live_server, settings, username=manager.username)

    url = reverse("shuup_admin:shop_product.new")
    browser.visit("%s%s" % (live_server, url))

    sku = "testsku"
    name = "Some product name"
    price_value = 10
    short_description = "short but gold"

    browser.fill("base-sku", sku)
    browser.fill("base-name__en", name)
    browser.fill("base-short_description__en", short_description)
    browser.fill("shop%s-default_price_value" % shop.pk, price_value)

    wait_until_appeared(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    click_element(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    wait_until_appeared(browser, "#create-object-iframe")

    # no permission to add category
    with browser.get_iframe("create-object-iframe") as iframe:
        error = "Can't view this page. You do not have the required permissions: category.new"
        wait_until_condition(iframe, condition=lambda x: x.is_text_present(error))

    # close iframe
    click_element(browser, "#create-object-overlay a.close-btn")

    # add permission to add category
    manager_permissions.add("category.new")
    manager_permissions.add("category.edit")
    set_permissions_for_group(manager_group, manager_permissions)

    # click to add category again
    click_element(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    wait_until_appeared(browser, "#create-object-iframe")

    # add the category
    with browser.get_iframe("create-object-iframe") as iframe:
        assert Category.objects.count() == 0
        wait_until_appeared(iframe, "input[name='base-name__en']")
        iframe.fill("base-name__en", "Test Category")
        time.sleep(3)  # Let's just wait here to the iFrame to open fully (for Chrome and headless)
        wait_until_appeared(iframe, "button[form='category_form']")
        click_element(browser, "button[form='category_form']")
        wait_until_condition(browser, condition=lambda x: Category.objects.count() == 1, timeout=20)

    assert Category.objects.first().name == "Test Category"

    # remove the edit category permissions
    # add permission to add category
    manager_permissions.remove("category.edit")
    set_permissions_for_group(manager_group, manager_permissions)

    # click to edit the button
    click_element(browser, "#id_shop%d-primary_category ~ .edit-object-btn a.btn" % shop.id)

    # no permission to edit category
    with browser.get_iframe("create-object-iframe") as iframe:
        error = "Can't view this page. You do not have the required permission(s): `category.edit`."
        wait_until_condition(iframe, condition=lambda x: x.is_text_present(error))

    # close iframe
    click_element(browser, "#create-object-overlay a.close-btn")

    manager_permissions.add("category.edit")
    set_permissions_for_group(manager_group, manager_permissions)

    click_element(browser, "#id_shop%d-primary_category ~ .edit-object-btn a.btn" % shop.id)
    wait_until_appeared(browser, "#create-object-iframe")

    new_cat_name = "Changed Name"
    with browser.get_iframe("create-object-iframe") as iframe:
        wait_until_appeared(iframe, "input[name='base-name__en']")
        iframe.fill("base-name__en", new_cat_name)
        time.sleep(3)  # Let's just wait here to the iFrame to open fully (for Chrome and headless)
        wait_until_appeared(iframe, "button[form='category_form']")
        click_element(browser, "button[form='category_form']")

    wait_until_condition(browser, condition=lambda x: Category.objects.first().name == new_cat_name, timeout=20)
