# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

import pytest
from django.core.urlresolvers import reverse

from shoop.core.models import Order
from shoop.testing.factories import (
    create_default_order_statuses, get_address, get_default_supplier
)
from shoop.testing.mock_population import populate_if_required
from shoop.testing.soup_utils import extract_form_fields
from shoop_tests.utils import SmartClient


def fill_address_inputs(soup, with_company=False):
    inputs = {}
    test_address = get_address()
    for key, value in extract_form_fields(soup.find('form', id='addresses')).items():
        if not value:
            if key in ("order-tax_number", "order-company_name"):
                continue
            if key.startswith("shipping-") or key.startswith("billing-"):
                bit = key.split("-")[1]
                value = getattr(test_address, bit, None)
            if not value and "email" in key:
                value = "test%d@example.shoop.io" % random.random()
            if not value:
                value = "test"
        inputs[key] = value

    if with_company:
        inputs["company-tax_number"] = "FI1234567-1"
        inputs["company-company_name"] = "Example Oy"
    else:
        inputs = dict((k, v) for (k, v) in inputs.items() if not k.startswith("company-"))

    return inputs


def _populate_client_basket(client):
    index = client.soup("/")
    product_links = index.find_all("a", rel="product-detail")
    assert product_links
    product_detail_path = product_links[0]["href"]
    assert product_detail_path
    product_detail_soup = client.soup(product_detail_path)
    inputs = extract_form_fields(product_detail_soup)
    basket_path = reverse("shoop:basket")
    for i in range(3):  # Add the same product thrice
        add_to_basket_resp = client.post(basket_path, data={
            "command": "add",
            "product_id": inputs["product_id"],
            "quantity": 1,
            "supplier": get_default_supplier().pk
        })
        assert add_to_basket_resp.status_code < 400
    basket_soup = client.soup(basket_path)
    assert b'no such element' not in basket_soup.renderContents(), 'All product details are not rendered correctly'


@pytest.mark.django_db
@pytest.mark.parametrize("with_company", [False, True])
def test_basic_order_flow(with_company):
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    c = SmartClient()
    _populate_client_basket(c)

    addresses_path = reverse("shoop:checkout", kwargs={"phase": "addresses"})
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup, with_company=with_company)
    response = c.post(addresses_path, data=inputs)
    assert response.status_code == 302  # Should redirect forth

    methods_path = reverse("shoop:checkout", kwargs={"phase": "methods"})
    methods_soup = c.soup(methods_path)
    assert c.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

    confirm_path = reverse("shoop:checkout", kwargs={"phase": "confirm"})
    confirm_soup = c.soup(confirm_path)
    assert c.post(confirm_path, data=extract_form_fields(confirm_soup)).status_code == 302  # Should redirect forth

    n_orders_post = Order.objects.count()
    assert n_orders_post > n_orders_pre, "order was created"
