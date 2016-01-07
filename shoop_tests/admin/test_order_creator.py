# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import json

import pytest
from django.test import RequestFactory
from django.utils import translation

from shoop.admin.modules.orders.views.create import (
    encode_address, encode_method, OrderCreateView
)
from shoop.core.models import Order, OrderLineType, Tax, TaxClass
from shoop.default_tax.models import TaxRule
from shoop.testing.factories import (
    create_product, create_random_company, create_random_person,
    get_default_payment_method, get_default_shipping_method, get_default_shop,
    get_default_supplier, get_initial_order_status
)
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils import assert_contains, printable_gibberish

TEST_COMMENT = "Hello. Is it me you're looking for?"


def get_frontend_order_state(contact, valid_lines=True):
    """
    Get a dict structure mirroring what the frontend JavaScript would submit.
    :type contact: Contact|None
    """
    translation.activate("en")
    shop = get_default_shop()
    tax = Tax.objects.create(code="test_code", rate=decimal.Decimal("0.20"), name="Default")
    tax_class = TaxClass.objects.create(identifier="test_tax_class", name="Default")
    rule = TaxRule.objects.create(tax=tax)
    rule.tax_classes.add(tax_class)
    rule.save()
    product = create_product(
        sku=printable_gibberish(),
        supplier=get_default_supplier(),
        shop=shop
    )
    product.tax_class = tax_class
    product.save()
    if valid_lines:
        lines = [
            {"id": "x", "type": "product", "product": {"id": product.id}, "quantity": "32", "baseUnitPrice": 50},
            {"id": "y", "type": "other", "sku": "hello", "text": "A greeting", "quantity": 1, "unitPrice": "5.5"},
            {"id": "z", "type": "text", "text": "This was an order!", "quantity": 0},
        ]
    else:
        unshopped_product = create_product(sku=printable_gibberish(), supplier=get_default_supplier())
        not_visible_product = create_product(
            sku=printable_gibberish(),
            supplier=get_default_supplier(),
            shop=shop
        )
        not_visible_shop_product = not_visible_product.get_shop_instance(shop)
        not_visible_shop_product.visible = False
        not_visible_shop_product.save()
        lines = [
            {"id": "x", "type": "product"},  # no product?
            {"id": "x", "type": "product", "product": {"id": unshopped_product.id}},  # not in this shop?
            {"id": "y", "type": "product", "product": {"id": -product.id}},  # invalid product?
            {"id": "z", "type": "other", "quantity": 1, "unitPrice": "q"},  # what's that price?
            {"id": "rr", "type": "product", "quantity": 1, "product": {"id": not_visible_product.id}}  # not visible
        ]

    state = {
        "customer": {"id": contact.id if contact else None},
        "lines": lines,
        "methods": {
            "shippingMethod": {"id": get_default_shipping_method().id},
            "paymentMethod": {"id": get_default_payment_method().id},
        },
        "shop": {
            "selected": {
                "id": shop.id,
                "name": shop.name,
                "currency": shop.currency,
                "priceIncludeTaxes": shop.prices_include_tax
            }
        }
    }
    return state


def get_frontend_request_for_command(state, command, user):
    json_data = json.dumps({"state": state})
    return apply_request_middleware(RequestFactory().post(
        "/",
        data=json_data,
        content_type="application/json; charset=UTF-8",
        QUERY_STRING="command=%s" % command
    ), user=user)


def get_order_from_state(state, admin_user):
    request = get_frontend_request_for_command(state, "create", admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "orderIdentifier")  # this checks for status codes as a side effect
    data = json.loads(response.content.decode("utf8"))
    return Order.objects.get(identifier=data["orderIdentifier"])


def test_order_creator_valid(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    order = get_order_from_state(get_frontend_order_state(contact), admin_user)
    assert order.lines.count() == 5  # 3 submitted, two for the shipping and payment method
    assert order.creator == admin_user
    assert order.customer == contact

    # Check that product line have right taxes
    for line in order.lines.all():
        if line.type == OrderLineType.PRODUCT:
            assert [line_tax.tax.code for line_tax in line.taxes.all()] == ["test_code"]
            assert line.taxful_price.amount > line.taxless_price.amount


def test_order_creator_invalid_base_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    state = get_frontend_order_state(contact=None)
    # Remove some critical data...
    state["customer"]["id"] = None
    state["shop"]["selected"]["id"] = None
    request = get_frontend_request_for_command(state, "create", admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "errorMessage", status_code=400)


def test_order_creator_invalid_line_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    state = get_frontend_order_state(contact=contact, valid_lines=False)
    request = get_frontend_request_for_command(state, "create", admin_user)
    response = OrderCreateView.as_view()(request)
    # Let's see that we get a cornucopia of trouble:
    assert_contains(response, "does not exist", status_code=400)
    assert_contains(response, "does not have a product", status_code=400)
    assert_contains(response, "is not available", status_code=400)
    assert_contains(response, "The price", status_code=400)
    assert_contains(response, "The quantity", status_code=400)
    assert_contains(response, "not visible", status_code=400)


def test_order_creator_view_GET(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "shippingMethods")  # in the config
    assert_contains(response, "shops")  # in the config


def test_order_creator_view_invalid_command(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/", {"command": printable_gibberish()}), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "unknown command", status_code=400)


def test_order_creator_product_data(rf, admin_user):
    shop = get_default_shop()
    product = create_product(sku=printable_gibberish(), supplier=get_default_supplier(), shop=shop)
    request = apply_request_middleware(rf.get("/", {
        "command": "product_data",
        "shop_id": shop.id,
        "id": product.id,
        "quantity": 42
    }), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "taxClass")
    assert_contains(response, "sku")
    assert_contains(response, product.sku)


def test_order_creator_customer_data(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = apply_request_middleware(rf.get("/", {
        "command": "customer_data",
        "id": contact.id
    }), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "name")
    assert_contains(response, contact.name)


def test_order_creator_source_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = get_frontend_request_for_command(get_frontend_order_state(contact), "source_data", admin_user)
    response = OrderCreateView.as_view()(request)
    data = json.loads(response.content.decode("utf8"))
    assert len(data.get("orderLines")) == 5


@pytest.mark.django_db
def test_encode_method_weights():
    payment_method = get_default_payment_method()
    assert encode_method(payment_method).get("minWeight") is None
    shipping_method = get_default_shipping_method()
    assert encode_method(shipping_method).get("minWeight") is None


def test_person_contact_creation(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    state = get_frontend_order_state(contact=contact)
    state["customer"] = {
        "id": None,
        "name": None,
        "billingAddress": encode_address(contact.default_billing_address),
        "shipToBillingAddress": True,
        "saveAddress": True,
        "isCompany": False
    }
    order = get_order_from_state(state, admin_user)
    assert order.lines.count() == 5
    assert order.customer.id != contact.id
    assert order.customer.name == contact.name
    assert order.billing_address.name == contact.default_billing_address.name
    assert order.billing_address.street == contact.default_billing_address.street
    assert order.billing_address.street == order.shipping_address.street


def test_company_contact_creation(rf, admin_user):
    get_initial_order_status()
    contact = create_random_company()
    test_tax_number = "1234567-1"
    contact.tax_number = test_tax_number
    contact.save()
    contact.default_billing_address.tax_number = test_tax_number
    contact.default_billing_address.save()
    state = get_frontend_order_state(contact=contact)
    state["customer"] = {
        "id": None,
        "name": None,
        "billingAddress": encode_address(contact.default_billing_address),
        "shipToBillingAddress": True,
        "saveAddress": True,
        "isCompany": True
    }
    order = get_order_from_state(state, admin_user)
    assert order.lines.count() == 5
    assert order.customer.id != contact.id
    assert order.customer.name == contact.name
    assert order.customer.tax_number == test_tax_number
    assert order.billing_address.tax_number == contact.default_billing_address.tax_number
    assert order.billing_address.street == contact.default_billing_address.street
    assert order.billing_address.street == order.shipping_address.street
