# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait


def wait_until_disappeared(browser, css_selector, timeout=30, frequency=1.0):
    """
    Wait until the element has disappeared

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_selector: String representation of the css selector
    :type css_selector: str
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
    ).until_not(lambda x: x.find_element_by_css_selector(css_selector).is_displayed())


def wait_until_appeared(browser, css_selector, timeout=30, frequency=1.0):
    """
    Wait until the element has appeared

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_selector: String representation of the css selector
    :type css_selector: str
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
    ).until(lambda x: x.find_element_by_css_selector(css_selector).is_displayed())


def move_to_element(browser, css_selector):
    """
    Scroll the browser window to the element

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_selector: String representation of the css selector
    :type css_selector: str
    :type css selector: callable
    """
    element = browser.driver.find_element_by_css_selector(css_selector)
    ActionChains(browser.driver).move_to_element(element).perform()
