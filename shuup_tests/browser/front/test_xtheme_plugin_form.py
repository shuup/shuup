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
from django.test.utils import override_settings
from django.utils.translation import activate, get_language

from shuup.testing import factories
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    page_has_loaded,
    wait_until_appeared,
    wait_until_condition,
)

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.parametrize("default_language", ["it", "pt-br", "fi"])
@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_plugin_form_language_order(admin_user, browser, live_server, settings, default_language):
    """
    Test that the first language option is the Parler default

    As you can see, we check for that the page has loaded and we use a sleep of 1 second.
    This is necessary specially into iframes. On this test, when we click to add a new plugin row
    or after a row selection, the iframe content is changed through a request,
    like a internal link when user clicks on a anchor. We have to make sure the NEW content is loaded
    before doing any element check, because it looks like the iframe won't find the correct elements
    if you start checking that before the new content gets loaded.
    """
    with override_settings(PARLER_DEFAULT_LANGUAGE_CODE=default_language):
        browser = initialize_admin_browser_test(browser, live_server, settings)
        browser.visit(live_server + "/")

        # Start edit
        wait_until_condition(browser, lambda x: page_has_loaded(x), timeout=20)
        wait_until_appeared(browser, ".xt-edit-toggle button[type='submit']")
        click_element(browser, ".xt-edit-toggle button[type='submit']")

        placeholder_selector = "#xt-ph-front_content-xtheme-person-contact-layout"
        placeholder_name = "front_content"
        wait_until_condition(browser, lambda x: x.is_element_present_by_css(placeholder_selector))
        click_element(browser, placeholder_selector)

        with browser.get_iframe("xt-edit-sidebar-iframe") as iframe:
            # make sure all scripts are loaded
            wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

            wait_until_condition(iframe, lambda x: x.is_text_present("Edit Placeholder: %s" % placeholder_name))
            wait_until_appeared(iframe, "button.layout-add-row-btn")
            time.sleep(1)
            wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

            # click to add a new row
            click_element(iframe, "button.layout-add-row-btn")
            time.sleep(1)
            wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

            # select the last row (the added one)
            click_element(iframe, "button.layout-add-row-btn")
            iframe.find_by_css("div.layout-cell").last.click()
            time.sleep(1)
            wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

            # select the TextPlugin
            wait_until_appeared(iframe, "select[name='general-plugin']")
            click_element(iframe, "#select2-id_general-plugin-container")
            wait_until_appeared(iframe, "input.select2-search__field")
            iframe.find_by_css("input.select2-search__field").first.value = "Text"
            wait_until_appeared(browser, ".select2-results__option:not([aria-live='assertive'])")
            iframe.execute_script('$($(".select2-results__option")[1]).trigger({type: "mouseup"})')

            time.sleep(1)
            wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)
            wait_until_appeared(iframe, "ul.editor-tabs")

            # check the languages order
            languages = [el.text for el in iframe.find_by_css("ul.editor-tabs li a")]
            assert languages[0] == default_language


@pytest.mark.parametrize("language", ["it", "pt-br", "fi", "en"])
@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_plugin_form_selected_language_pane(admin_user, browser, live_server, settings, language):
    """
    Test that the current language is selected by default
    """
    browser = initialize_admin_browser_test(browser, live_server, settings, language=language)
    browser.visit(live_server + "/")

    # Start edit
    wait_until_condition(browser, lambda x: page_has_loaded(x), timeout=20)
    wait_until_appeared(browser, ".xt-edit-toggle button[type='submit']")
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    placeholder_selector = "#xt-ph-front_content-xtheme-person-contact-layout"
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(placeholder_selector))
    click_element(browser, placeholder_selector)

    with browser.get_iframe("xt-edit-sidebar-iframe") as iframe:
        # make sure all scripts are loaded
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        wait_until_condition(iframe, lambda x: x.is_text_present("front_content"))
        wait_until_appeared(iframe, "button.layout-add-row-btn")
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        # click to add a new row
        click_element(iframe, "button.layout-add-row-btn")
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        # select the last row (the added one)
        click_element(iframe, "button.layout-add-row-btn")
        iframe.find_by_css("div.layout-cell").last.click()
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        # select the TextPlugin
        wait_until_appeared(iframe, "select[name='general-plugin']")
        click_element(iframe, "#select2-id_general-plugin-container")
        wait_until_appeared(iframe, "input.select2-search__field")
        iframe.find_by_css("input.select2-search__field").first.value = "Text"
        wait_until_appeared(browser, ".select2-results__option:not([aria-live='assertive'])")
        iframe.execute_script('$($(".select2-results__option")[1]).trigger({type: "mouseup"})')
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)
        wait_until_appeared(iframe, "ul.editor-tabs")

        # check the active language
        assert language == iframe.find_by_css("ul.editor-tabs li.active a").first.text


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_xtheme_editor_form_picture(admin_user, browser, live_server, settings):
    """
    Test that is is possible to add image fron media browser
    """
    browser = initialize_admin_browser_test(browser, live_server, settings)
    browser.visit(live_server + "/")

    wait_until_condition(browser, lambda x: page_has_loaded(x), timeout=20)
    wait_until_appeared(browser, ".xt-edit-toggle button[type='submit']")
    click_element(browser, ".xt-edit-toggle button[type='submit']")

    placeholder_selector = "#xt-ph-front_content-xtheme-person-contact-layout"
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(placeholder_selector))
    click_element(browser, placeholder_selector)

    with browser.get_iframe("xt-edit-sidebar-iframe") as iframe:
        # make sure all scripts are loaded
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        wait_until_condition(iframe, lambda x: x.is_text_present("front_content"))
        wait_until_appeared(iframe, "button.layout-add-row-btn")
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        # click to add a new row
        click_element(iframe, "button.layout-add-row-btn")
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        # select the last row (the added one)
        click_element(iframe, "button.layout-add-row-btn")
        iframe.find_by_css("div.layout-cell").last.click()
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)

        # select the TextPlugin
        wait_until_appeared(iframe, "select[name='general-plugin']")
        iframe.select("general-plugin", "text")
        time.sleep(1)
        wait_until_condition(iframe, lambda x: page_has_loaded(x), timeout=20)
        wait_until_appeared(iframe, "ul.editor-tabs")

        filer_image = factories.get_random_filer_image()

        wait_until_appeared(browser, "#id_plugin-text_en-editor-wrap button[aria-label='Picture']")
        click_element(browser, "#id_plugin-text_en-editor-wrap button[aria-label='Picture']")
        wait_until_condition(browser, lambda b: len(b.windows) == 2, timeout=20)

        # change to the media browser window
        browser.windows.current = browser.windows[1]

        # click to select the picture
        wait_until_appeared(browser, "a.file-preview")
        browser.find_by_css("a.file-preview").first.click()

        # back to the main window
        wait_until_condition(browser, lambda b: len(b.windows) == 1)
        browser.windows.current = browser.windows[0]

        # make sure the image was added to the editor
        wait_until_appeared(
            browser, "#id_plugin-text_en-editor-wrap .note-editable img[src='%s']" % filer_image.url, timeout=20
        )
