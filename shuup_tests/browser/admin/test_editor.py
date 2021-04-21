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

from shuup.testing import factories
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    move_to_element,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_summernote_editor_picture(browser, admin_user, live_server, settings):
    activate("en")
    factories.get_default_shop()
    factories.get_default_product_type()
    factories.get_default_sales_unit()
    factories.get_default_tax_class()
    filer_image = factories.get_random_filer_image()

    initialize_admin_browser_test(browser, live_server, settings)
    original_size = browser.driver.get_window_size()
    browser.driver.set_window_size(1920, 1080)

    url = reverse("shuup_admin:shop_product.new")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("New shop product"))

    img_icon_selector = "#id_base-description__en-editor-wrap i[class='note-icon-picture']"
    move_to_element(browser, img_icon_selector)
    click_element(browser, img_icon_selector)
    wait_until_condition(browser, lambda b: len(b.windows) == 2)

    # change to the media browser window
    browser.windows.current = browser.windows[1]

    # click to select the picture
    wait_until_appeared(browser, "a.file-preview")
    click_element(browser, "a.file-preview")

    # back to the main window
    wait_until_condition(browser, lambda b: len(b.windows) == 1)
    browser.windows.current = browser.windows[0]

    # make sure the image was added to the editor
    wait_until_appeared(
        browser, "#id_base-description__en-editor-wrap .note-editable img[src='%s']" % filer_image.url, timeout=20
    )
    browser.driver.set_window_size(original_size["width"], original_size["height"])
