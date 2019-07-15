# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import json
import pytest

from django.core.urlresolvers import reverse

from shuup import configuration
from shuup.core import cache
from shuup.core.models import (
    ProductMode, ProductVariationVariable, ProductVariationVariableValue
)
from shuup.testing.browser_utils import (
    click_element, initialize_admin_browser_test, wait_until_condition
)
from shuup.testing.factories import create_product, get_default_shop


from shuup_tests.utils import printable_gibberish


pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_variation_templates(browser, admin_user, live_server, settings):
    cache.clear()  # Avoid cache from past tests
    shop = get_default_shop()
    configuration_key = "saved_variation_templates"
    assert configuration.get(shop, configuration_key, None) is None
    product = create_product("test_sku", shop, default_price=10, mode=ProductMode.VARIABLE_VARIATION_PARENT)
    assert product.is_variation_parent()
    initialize_admin_browser_test(browser, live_server, settings)
    browser.driver.set_window_size(800, 1000)
    url = reverse("shuup_admin:shop_product.edit_variation", kwargs={"pk": product.pk})
    browser.visit("%s%s" % (live_server, url + "#variables-section"))
    click_element(browser, '#variables-section > div:nth-child(1) > a:nth-child(2)')
    wait_until_condition(browser, lambda x: x.is_text_present("New template"))

    assert len(ProductVariationVariable.objects.filter(product=product)) == 0 # Size
    assert len(ProductVariationVariableValue.objects.all()) == 0  # Assert no variations are active
    click_element(browser, '.fa.fa-plus')

    wait_until_condition(browser, lambda x: x.is_text_present("New template"))
    browser.fill("variables-template_name", printable_gibberish())  # variables-template_name
    click_element(browser, '#save_template_name')
    wait_until_condition(browser, lambda x: not x.is_text_present("New template"))
    assert len(configuration.get(shop, configuration_key, [])) == 1
    click_element(browser, '#variables-section > div:nth-child(1) > a:nth-child(2)')
    click_element(browser, "#variation-variable-editor")
    browser.find_by_xpath('//*[@id="variation-variable-editor"]/div/div/select/option[2]').first.click()
    wait_until_condition(browser, lambda x: x.is_text_present("Add new variable"))
    click_element(browser, ".btn.btn-lg.btn-text")
    browser.find_by_xpath('//*[@id="product-variable-wrap"]/div/div[2]/div[1]/table/tbody[1]/tr/td[1]/input').first.fill("Size")
    click_element(browser, ".btn.btn-xs.btn-text")
    browser.find_by_xpath('//*[@id="product-variable-wrap"]/div/div[2]/div[1]/table/tbody[2]/tr/td[1]/input').first.fill("S")
    click_element(browser, "#id_variables-activate_template")  # Activate template
    click_element(browser, ".fa.fa-check-circle")  # Save

    assert len(ProductVariationVariable.objects.filter(product=product)) == 1 # Size
    assert len(ProductVariationVariableValue.objects.all()) == 1  # S

    click_element(browser, '#variables-section > div:nth-child(1) > a:nth-child(2)')
    click_element(browser, "#variation-variable-editor") # id_variables-data
    cache.clear()  # Avoid cache from past tests
    assert len(configuration.get(shop, configuration_key, [])) == 1

    browser.find_by_xpath('//*[@id="variation-variable-editor"]/div/div/select/option[2]').first.click()
    template_data = configuration.get(shop, configuration_key, [])[0].get('data')[0]
    browser_data = json.loads(browser.find_by_css("#id_variables-data").value).get('variable_values')[0]
    assert browser_data == template_data  # assert shown template data matches template data in the db
