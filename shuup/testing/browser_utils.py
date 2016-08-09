# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.support.wait import WebDriverWait


def wait_until_disappeared(browser, css_class, timeout=30, frequency=1.0):
    """
    Wait until the element has disappeared

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_class: String representation of the css class(es)
    :type css_class: str
    :param timeout: Time to wait for element to disappear
    :type timeout: int
    :param frequency: Polling frequency
    :type frequency: float
    """
    WebDriverWait(
        browser.driver,
        timeout=timeout,
        poll_frequency=frequency,
        ignored_exceptions=(ElementNotVisibleException)
    ).until_not(lambda x: x.find_element_by_css_selector(css_class).is_displayed())


def wait_until_appeared(browser, css_class, timeout=30, frequency=1.0):
    """
    Wait until the element has appeared

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_class: String representation of the css class(es)
    :type css_class: str
    :param timeout: Time to wait for element to appear
    :type timeout: int
    :param frequency: Polling frequency
    :type frequency: float
    """
    WebDriverWait(
        browser.driver,
        timeout=timeout,
        poll_frequency=frequency,
        ignored_exceptions=(ElementNotVisibleException)
    ).until(lambda x: x.find_element_by_css_selector(css_class).is_displayed())
