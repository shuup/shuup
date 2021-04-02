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

from shuup.admin.modules.orders.views.addresses import ADDRESS_EDITED_LOG_IDENTIFIER
from shuup.core.models import OrderStatus
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.testing.factories import create_empty_order, get_default_shop
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
def test_product_detail(browser, admin_user, live_server, settings):
    activate(settings.PARLER_DEFAULT_LANGUAGE_CODE)
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()
    initialize_admin_browser_test(browser, live_server, settings)
    url = reverse("shuup_admin:order.detail", kwargs={"pk": order.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Order %s" % order.pk))

    change_addresses(live_server, browser, order)

    set_status(browser, order, OrderStatus.objects.get_default_processing())
    assert order.can_set_complete()
    set_status(browser, order, OrderStatus.objects.get_default_complete())


def change_addresses(live_server, browser, order):
    edit_url = reverse("shuup_admin:order.edit-addresses", kwargs={"pk": order.pk})
    browser.visit("%s%s" % (live_server, edit_url))
    order_edited_log_entries = order.log_entries.filter(identifier=ADDRESS_EDITED_LOG_IDENTIFIER).count()

    edit_address_title = "Save -- Order %s" % order.pk
    wait_until_condition(browser, condition=lambda x: x.is_text_present(edit_address_title))
    # Do nothing just hit the save
    click_element(browser, "button[form='edit-addresses']")
    assert order.log_entries.filter(identifier=ADDRESS_EDITED_LOG_IDENTIFIER).count() == order_edited_log_entries

    # Update billing address email
    browser.visit("%s%s" % (live_server, edit_url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present(edit_address_title))
    new_email = "somerandomemail@example.com"
    browser.fill("billing_address-email", new_email)
    assert new_email != order.billing_address.email
    click_element(browser, "button[form='edit-addresses']")
    check_log_entries_count(browser, order, order_edited_log_entries + 1)

    order.refresh_from_db()
    assert new_email == order.billing_address.email
    assert order.billing_address.email != order.shipping_address.email
    assert order.billing_address.pk != order.shipping_address.pk

    # Update shipping address postal code
    browser.visit("%s%s" % (live_server, edit_url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present(edit_address_title))
    new_postal_code = "20540"
    browser.fill("shipping_address-postal_code", new_postal_code)
    assert new_postal_code != order.shipping_address.postal_code
    click_element(browser, "button[form='edit-addresses']")
    check_log_entries_count(browser, order, order_edited_log_entries + 2)

    order.refresh_from_db()
    assert new_postal_code == order.shipping_address.postal_code
    assert order.billing_address.postal_code != order.shipping_address.postal_code
    assert order.billing_address.pk != order.shipping_address.pk

    # Now update both same time
    browser.visit("%s%s" % (live_server, edit_url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present(edit_address_title))
    new_name = "%s (edited)" % order.billing_address.name
    browser.fill("billing_address-name", new_name)
    click_element(browser, "#billing-to-shipping")
    click_element(browser, "button[form='edit-addresses']")
    check_log_entries_count(browser, order, order_edited_log_entries + 4)
    order.refresh_from_db()
    assert new_name == order.shipping_address.name
    assert order.billing_address.name == order.shipping_address.name
    assert order.billing_address.email == order.shipping_address.email


def set_status(browser, order, status):
    click_element(browser, "button.set-status-button")
    form_action = reverse("shuup_admin:order.set-status", kwargs={"pk": order.pk})
    click_element(browser, "button[formaction='%s'][value='%s']" % (form_action, status.pk))
    wait_until_appeared(browser, "div[class='message success']")
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Order %s" % order.pk))
    order.refresh_from_db()
    assert order.status.pk == status.pk


def check_log_entries_count(browser, order, target_count):
    wait_until_condition(
        browser,
        condition=lambda x: order.log_entries.filter(identifier=ADDRESS_EDITED_LOG_IDENTIFIER).count() == target_count,
    )
