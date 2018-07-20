# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from selenium.common.exceptions import (
    ElementNotVisibleException, StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.wait import WebDriverWait


def wait_until_disappeared(browser, css_selector, timeout=10, frequency=1.0):
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
    wait_until_condition(
        browser,
        condition=lambda x: not x.driver.find_element_by_css_selector(css_selector).is_displayed(),
        timeout=timeout,
        frequency=frequency)


def wait_until_appeared(browser, css_selector, timeout=10, frequency=1.0):
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
    wait_until_condition(
        browser,
        condition=lambda x: x.driver.find_element_by_css_selector(css_selector).is_displayed(),
        timeout=timeout,
        frequency=frequency)


def wait_until_appeared_xpath(browser, xpath, timeout=10, frequency=1.0):
    wait_until_condition(
        browser,
        condition=lambda x: x.driver.find_element_by_xpath(xpath).is_displayed(),
        timeout=timeout,
        frequency=frequency)


def wait_until_condition(browser, condition, timeout=10, frequency=1.0):
    """
    Wait until the condition has been met

    :param browser:
    :type browser: splinter.browser.Browser
    :param condition: callable that takes a splinter.browser.Browser
                      and returns a boolean indicating whether the condition has been met
    :type css_selector: callable
    :param timeout: Time to wait for element to appear
    :type timeout: int
    :param frequency: Polling frequency
    :type frequency: float
    """
    WebDriverWait(
        browser.driver,
        timeout=timeout,
        poll_frequency=frequency,
        ignored_exceptions=(ElementNotVisibleException, StaleElementReferenceException)
    ).until(lambda x: condition(browser))


def move_to_element(browser, css_selector, header_height=155):
    """
    Scroll the browser window to the element

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_selector: String representation of the css selector
    :type css_selector: str
    """
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(css_selector))
    element = browser.driver.find_element_by_css_selector(css_selector)
    y = element.location["y"] - header_height
    browser.execute_script("window.scrollTo(0, %s)" % y)


def click_element(browser, css_selector, timeout=10, frequency=1.0, header_height=155):
    """
    Click a browser DOM element

    :param browser:
    :type browser: splinter.browser.Browser
    :param css_selector: String representation of the css selector
    :type css_selector: str
    :param timeout: Time to wait for element to appear
    :type timeout: int
    :param frequency: Polling frequency
    :type frequency: float
    """
    move_to_element(browser, css_selector, header_height)
    # selenium weirdness when clicking a button that already has focus...grumble grumble
    # http://stackoverflow.com/questions/21330894/why-do-i-have-to-click-twice-to-a-submit-input-using-selenium
    browser.execute_script('document.querySelector("%s").focus()' % css_selector.replace('"', '\\"'))
    wait_until_condition(
        browser,
        condition=lambda x: EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))(browser.driver),
        timeout=timeout,
        frequency=frequency)
    browser.find_by_css(css_selector).click()


def page_has_loaded(browser):
    """
    Returns whether the page has loaded

    :param browser:
    :type browser: splinter.browser.Browser
    :rtype bool
    """
    return browser.evaluate_script("document.readyState") == "complete"
