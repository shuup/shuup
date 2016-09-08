# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest

from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.admin.signals import object_created
from shuup.core.models import Product
from shuup.testing.browser_utils import click_element, wait_until_appeared
from shuup.testing.factories import (
    create_product, get_default_product_type, get_default_sales_unit,
    get_default_shop, get_default_tax_class
)
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")
OBJECT_CREATED_LOG_IDENTIFIER = "object_created_signal_handled"


@pytest.mark.browser
@pytest.mark.djangodb
def test_product_create(browser, admin_user, live_server):
    activate("en")
    shop = get_default_shop()
    get_default_product_type()
    get_default_sales_unit()
    get_default_tax_class()
    object_created.connect(_add_custom_product_created_message, sender=Product, dispatch_uid="object_created_signal_test")
    initialize_admin_browser_test(browser, live_server)

    url = reverse("shuup_admin:product.new")
    browser.visit("%s%s" % (live_server, url))
    sku = "testsku"
    name = "Some product name"
    price_value = 10

    browser.fill("base-sku", sku)
    browser.fill("base-name__en", name)
    browser.fill("shop%s-default_price_value" % shop.pk, price_value)

    click_element(browser, "button[form='product_form']")
    wait_until_appeared(browser, "div[class='message success']")
    Product.objects.filter(sku=sku).first().log_entries.filter(identifier=OBJECT_CREATED_LOG_IDENTIFIER).count() == 1
    object_created.disconnect(sender=Product, dispatch_uid="object_created_signal_test")


def _add_custom_product_created_message(sender, object, **kwargs):
    assert sender == Product
    object.add_log_entry("Custom object created signal handled", identifier=OBJECT_CREATED_LOG_IDENTIFIER)
