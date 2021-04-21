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

from shuup.front.apps.carousel.models import Carousel
from shuup.testing import factories
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_carousel_create(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    filer_image = factories.get_random_filer_image()
    factories.get_default_category()

    initialize_admin_browser_test(browser, live_server, settings, shop=shop)
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))

    assert not Carousel.objects.exists()

    browser.visit(live_server + "/sa/carousels/new")
    wait_until_condition(browser, lambda x: x.is_text_present("New Carousel"))
    browser.fill("base-name", "Carrot")
    click_element(browser, "button[form='carousel_form']")
    wait_until_appeared(browser, "div[class='message success']")

    assert Carousel.objects.count() == 1
    carousel = Carousel.objects.first()

    browser.visit(live_server + "/sa/carousels/%d/" % carousel.pk)
    time.sleep(1)
    wait_until_condition(browser, lambda x: x.is_text_present(carousel.name))
    click_element(browser, "a[href='#slides-section']")
    wait_until_appeared(browser, ".slide-add-new-panel")

    # add 1 slide
    click_element(browser, ".slide-add-new-panel")
    wait_until_condition(browser, lambda x: x.is_text_present("Slide 1"))
    wait_until_appeared(browser, "a[href='#collapse1']")
    click_element(browser, "a[href='#collapse1']")

    browser.find_by_css("#slide_1-en [name='slides-__slide_prefix__-caption__en']").fill("New Slide")
    click_element(browser, "[name='slides-__slide_prefix__-category_link'] + .select2")
    wait_until_appeared(browser, ".select2-container #select2-id_slides-__slide_prefix__-category_link-results li")
    click_element(browser, ".select2-container #select2-id_slides-__slide_prefix__-category_link-results li:last-child")

    browser.find_by_css("#slide_1-en [data-dropzone='true']").click()
    wait_until_condition(browser, lambda b: len(b.windows) == 2)
    # change to the media browser window
    browser.windows.current = browser.windows[1]
    # click to select the picture
    wait_until_appeared(browser, "a.file-preview")
    click_element(browser, "a.file-preview")
    # back to the main window
    wait_until_condition(browser, lambda b: len(b.windows) == 1)
    browser.windows.current = browser.windows[0]
    wait_until_appeared(browser, ".dz-image img[alt='%s']" % filer_image.name)

    click_element(browser, "button[form='carousel_form']")
    wait_until_appeared(browser, "div[class='message success']")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_carousel_multi_slide(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    filer_image = factories.get_random_filer_image()

    initialize_admin_browser_test(browser, live_server, settings, shop=shop)
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))

    assert not Carousel.objects.exists()

    browser.visit(live_server + "/sa/carousels/new")
    wait_until_condition(browser, lambda x: x.is_text_present("New Carousel"))
    browser.fill("base-name", "Carrot")
    click_element(browser, "button[form='carousel_form']")
    wait_until_appeared(browser, "div[class='message success']")

    assert Carousel.objects.count() == 1
    carousel = Carousel.objects.first()

    browser.visit(live_server + "/sa/carousels/%d/" % carousel.pk)
    wait_until_condition(browser, lambda x: x.is_text_present(carousel.name))
    click_element(browser, "a[href='#slides-section']")
    wait_until_appeared(browser, ".slide-add-new-panel")

    # add 4 slides
    click_element(browser, ".slide-add-new-panel")
    click_element(browser, ".slide-add-new-panel")
    click_element(browser, ".slide-add-new-panel")
    click_element(browser, ".slide-add-new-panel")

    wait_until_condition(browser, lambda x: x.is_text_present("Slide 3"))

    # delete slide3
    wait_until_appeared(browser, "a[href='#collapse3']")
    click_element(browser, "a[href='#collapse3']")
    wait_until_appeared(browser, "#collapse3 .btn-remove-slide")
    click_element(browser, "#collapse3 .btn-remove-slide")

    wait_until_condition(browser, lambda x: not x.is_text_present("Slide 3"))
    click_element(browser, "button[form='carousel_form']")

    wait_until_appeared(browser, "a[href='#slides-section'].errors")
    click_element(browser, "a[href='#slides-section']")

    for slide_id in [0, 1, 2]:
        wait_until_appeared(browser, "a[href='#collapse%d']" % (slide_id + 1))
        click_element(browser, "a[href='#collapse%d']" % (slide_id + 1))

        browser.find_by_css("[name='slides-%d-caption__en']" % slide_id).fill("Slide")
        click_element(browser, "[name='slides-%d-category_link'] + .select2" % slide_id)
        wait_until_appeared(browser, ".select2-container #select2-id_slides-%d-category_link-results li" % slide_id)
        click_element(
            browser, ".select2-container #select2-id_slides-%d-category_link-results li:last-child" % slide_id
        )

        browser.find_by_css("#id_slides-%d-image__en-dropzone" % slide_id).click()
        wait_until_condition(browser, lambda b: len(b.windows) == 2)
        # change to the media browser window
        browser.windows.current = browser.windows[1]
        # click to select the picture
        wait_until_appeared(browser, "a.file-preview")
        click_element(browser, "a.file-preview")
        # back to the main window
        wait_until_condition(browser, lambda b: len(b.windows) == 1)
        browser.windows.current = browser.windows[0]
        wait_until_appeared(browser, ".dz-image img[alt='%s']" % filer_image.name)

    click_element(browser, "button[form='carousel_form']")
    wait_until_appeared(browser, "div[class='message success']")
