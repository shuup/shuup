# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
import selenium
import time

from shuup.core.models import get_person_contact
from shuup.testing import factories
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    page_has_loaded,
    wait_until_condition,
)
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_edit_front(admin_user, browser, live_server, settings):
    browser = initialize_admin_browser_test(browser, live_server, settings)  # Login to admin as admin user
    browser.visit(live_server + "/")
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    # Start edit
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    # Add some content only visible for person contacts
    person_contact_text_content = "This text is shown for person contacts only!"
    _edit_layout(
        browser, "front_content", "#xt-ph-front_content-xtheme-person-contact-layout", person_contact_text_content
    )

    browser.find_by_css("#admin-tools-menu li.dropdown").click()
    browser.find_by_css("a[href='/force-anonymous-contact/']").first.click()

    ## Add some content only visible for anonymous contacts
    anonymous_contact_text_content = "This text is shown for guests only!"
    _edit_layout(
        browser, "front_content", "#xt-ph-front_content-xtheme-anonymous-contact-layout", anonymous_contact_text_content
    )

    browser.find_by_css("#admin-tools-menu li.dropdown").click()
    browser.find_by_css("a[href='/force-company-contact/']").first.click()

    ### Add some content only visible for company contacts
    company_contact_text_content = "This text is shown for company contacts only!"
    _edit_layout(
        browser, "front_content", "#xt-ph-front_content-xtheme-company-contact-layout", company_contact_text_content
    )

    # Close edit
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    # Logout
    click_element(browser, "div.top-nav i.menu-icon.fa.fa-user")
    click_element(browser, "a[href='/logout/']")

    # Go to home and check content for anonymous contacts
    browser.visit(live_server + "/")
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    wait_until_condition(browser, lambda x: x.is_text_present(anonymous_contact_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(person_contact_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(company_contact_text_content))

    # Create user login and got check the content for person contact
    user = factories.create_random_user()
    password = "timo123"
    user.set_password(password)
    user.save()

    click_element(browser, "#login-dropdown")
    browser.fill("username", user.username)
    browser.fill("password", password)
    browser.find_by_css("ul.login button[type='submit']").click()

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    wait_until_condition(browser, lambda x: x.is_text_present(person_contact_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(anonymous_contact_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(company_contact_text_content))

    # Logout
    click_element(browser, "div.top-nav i.menu-icon.fa.fa-user")
    click_element(browser, "a[href='/logout/']")

    # Create person contact to company and re-login and check the content for companies
    company = factories.create_random_company()
    company.members.add(get_person_contact(user))

    click_element(browser, "#login-dropdown")
    browser.fill("username", user.username)
    browser.fill("password", password)
    browser.find_by_css("ul.login button[type='submit']").click()

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    wait_until_condition(browser, lambda x: x.is_text_present(company_contact_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(anonymous_contact_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(person_contact_text_content))


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_edit_product(admin_user, browser, live_server, settings):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    products = []
    for x in range(3):
        products.append(factories.create_product("test%s" % x, shop=shop, supplier=supplier, default_price=10))

    browser = initialize_admin_browser_test(browser, live_server, settings)  # Login to admin as admin user

    browser.visit(live_server + "/")
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    # Start edit
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    # Visit first product and edit the layout with custom text
    first_product = products.pop()
    first_product_url = "%s%s" % (
        live_server,
        reverse("shuup:product", kwargs={"pk": first_product.pk, "slug": first_product.slug}),
    )
    browser.visit(first_product_url)

    first_product_text_content = "This text is only visible for product %s." % first_product.name
    _edit_layout(
        browser,
        "product_extra_1",
        "#xt-ph-product_extra_1-xtheme-product-layout-%s" % first_product.pk,
        first_product_text_content,
    )

    # Visit second product and edit the layout with custom text
    second_product = products.pop()
    second_product_url = "%s%s" % (
        live_server,
        reverse("shuup:product", kwargs={"pk": second_product.pk, "slug": second_product.slug}),
    )
    browser.visit(second_product_url)

    second_product_text_content = "This text is only visible for product %s." % second_product.name
    _edit_layout(
        browser,
        "product_extra_1",
        "#xt-ph-product_extra_1-xtheme-product-layout-%s" % second_product.pk,
        second_product_text_content,
    )

    # Visit third product and edit common layout with text
    third_product = products.pop()
    third_product_url = "%s%s" % (
        live_server,
        reverse("shuup:product", kwargs={"pk": third_product.pk, "slug": third_product.slug}),
    )
    browser.visit(third_product_url)

    common_text_content = "This text is visible for all products."
    _edit_layout(browser, "product_extra_1", "#xt-ph-product_extra_1", common_text_content)

    # Close edit
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    # Logout
    click_element(browser, "div.top-nav i.menu-icon.fa.fa-user")
    click_element(browser, "a[href='/logout/']")

    # Let's revisit the product details as anonymous and check the placeholder content
    browser.visit(first_product_url)
    wait_until_condition(browser, lambda x: x.is_text_present(common_text_content))
    wait_until_condition(browser, lambda x: x.is_text_present(first_product_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(second_product_text_content))

    browser.visit(second_product_url)
    wait_until_condition(browser, lambda x: x.is_text_present(common_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(first_product_text_content))
    wait_until_condition(browser, lambda x: x.is_text_present(second_product_text_content))

    browser.visit(third_product_url)
    wait_until_condition(browser, lambda x: x.is_text_present(common_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(first_product_text_content))
    wait_until_condition(browser, lambda x: not x.is_text_present(second_product_text_content))


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_edit_save_and_publish(admin_user, browser, live_server, settings):
    browser = initialize_admin_browser_test(browser, live_server, settings)  # Login to admin as admin user
    browser.visit(live_server + "/")
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))

    # Start edit
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    # Add some content only visible for person contacts
    text_content = "Some dummy content!"
    layout_selector = "#xt-ph-front_content-xtheme-person-contact-layout"
    placeholder_name = "front_content"

    wait_until_condition(browser, lambda x: x.is_element_present_by_css(layout_selector))
    click_element(browser, layout_selector)
    with browser.get_iframe("xt-edit-sidebar-iframe") as iframe:
        wait_until_condition(iframe, lambda x: x.is_text_present("Edit Placeholder: %s" % placeholder_name))
        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("button.layout-add-row-btn"))
        click_element(iframe, "button.layout-add-row-btn")
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x))

        try:
            wait_until_condition(iframe, lambda x: x.is_element_present_by_css("div.layout-cell"))
        except selenium.common.exceptions.TimeoutException as e:  # Give the "Add new row" second chance
            click_element(iframe, "button.layout-add-row-btn")
            wait_until_condition(iframe, lambda x: x.is_element_present_by_css("div.layout-cell"))

        click_element(iframe, "div.layout-cell")

        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("select[name='general-plugin']"))
        iframe.select("general-plugin", "text")

        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("div.note-editable"))
        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("#id_plugin-text_en-editor-wrap"))
        iframe.execute_script(
            "$('#id_plugin-text_en-editor-wrap .summernote-editor').summernote('editor.insertText', '%s');"
            % text_content
        )

        click_element(iframe, "button.publish-btn")
        alert = iframe.get_alert()
        assert alert.text == "Are you sure you wish to publish changes made to this view?"
        alert.accept()

        time.sleep(1)

        alert = iframe.get_alert()
        assert alert.text == "You have changed the form. Do you want to save them before publishing?"
        alert.accept()

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    wait_until_condition(browser, lambda x: x.is_text_present(text_content))


def _edit_layout(browser, placeholder_name, layout_selector, text_content):
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(layout_selector))
    click_element(browser, layout_selector)
    with browser.get_iframe("xt-edit-sidebar-iframe") as iframe:
        wait_until_condition(iframe, lambda x: x.is_text_present("Edit Placeholder: %s" % placeholder_name))
        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("button.layout-add-row-btn"))
        click_element(iframe, "button.layout-add-row-btn")

        # Well the second click here makes it so that the next
        # timeout exception doesn't happen (often). For some reason
        # the button wasn't able to click when present. This is also
        # weird since outside the browser tests there is no reason
        # to expect that 'add row' is slower than other requests.
        click_element(iframe, "button.layout-add-row-btn")

        try:
            wait_until_condition(iframe, lambda x: x.is_element_present_by_css("div.layout-cell"))
        except selenium.common.exceptions.TimeoutException as e:  # Give the "Add new row" second chance
            click_element(iframe, "button.layout-add-row-btn")
            wait_until_condition(iframe, lambda x: x.is_element_present_by_css("div.layout-cell"))

        click_element(iframe, "div.layout-cell")

        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("select[name='general-plugin']"))
        iframe.select("general-plugin", "text")

        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("div.note-editable"))
        wait_until_condition(iframe, lambda x: x.is_element_present_by_css("#id_plugin-text_en-editor-wrap"))
        iframe.execute_script(
            "$('#id_plugin-text_en-editor-wrap .summernote-editor').summernote('editor.insertText', '%s');"
            % text_content
        )

        click_element(iframe, "button.submit-form-btn")
        click_element(iframe, "button.publish-btn")

        alert = iframe.get_alert()
        alert.accept()

    wait_until_condition(browser, lambda x: not x.is_element_present_by_css("#xt-edit-sidebar-iframe"))
