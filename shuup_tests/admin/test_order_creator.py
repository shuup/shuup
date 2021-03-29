# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import json
import pytest
from django.test import RequestFactory
from django.utils import translation
from django.utils.encoding import force_text

from shuup.admin.modules.orders.views.edit import OrderEditView, encode_address, encode_method
from shuup.core.models import Order, OrderLineType, ShopProductVisibility, Tax, TaxClass
from shuup.default_tax.models import TaxRule
from shuup.testing.factories import (
    UserFactory,
    create_empty_order,
    create_order_with_product,
    create_product,
    create_random_company,
    create_random_order,
    create_random_person,
    get_default_customer_group,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_initial_order_status,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.i18n import format_money
from shuup_tests.utils import assert_contains, printable_gibberish

TEST_COMMENT = "Hello. Is it me you're looking for?"


def get_frontend_order_state(contact, valid_lines=True):
    """
    Get a dict structure mirroring what the frontend JavaScript would submit.
    :type contact: Contact|None
    """
    translation.activate("en")
    shop = get_default_shop()
    tax, created = Tax.objects.get_or_create(
        code="test_code", defaults={"rate": decimal.Decimal("0.20"), "name": "Default"}
    )
    tax_class, created = TaxClass.objects.get_or_create(identifier="test_tax_class", defaults={"name": "Default"})
    rule, created = TaxRule.objects.get_or_create(tax=tax)
    rule.tax_classes.add(tax_class)
    rule.save()
    supplier = get_default_supplier()
    product = create_product(sku=printable_gibberish(), supplier=supplier, shop=shop)
    product.tax_class = tax_class
    product.save()
    if valid_lines:
        lines = [
            {
                "id": "x",
                "type": "product",
                "product": {"id": product.id},
                "supplier": {"name": supplier.name, "id": supplier.id},
                "quantity": "32",
                "baseUnitPrice": 50,
            },
            {
                "id": "y",
                "type": "other",
                "sku": "hello",
                "text": "A greeting",
                "supplier": {"name": supplier.name, "id": supplier.id},
                "quantity": 1,
                "unitPrice": "5.5",
            },
            {
                "id": "z",
                "type": "text",
                "text": "This was an order!",
                "supplier": {"name": supplier.name, "id": supplier.id},
                "quantity": 0,
            },
        ]
    else:
        unshopped_product = create_product(sku=printable_gibberish(), supplier=supplier)
        not_visible_product = create_product(sku=printable_gibberish(), supplier=supplier, shop=shop)
        not_visible_shop_product = not_visible_product.get_shop_instance(shop)
        not_visible_shop_product.visibility = ShopProductVisibility.NOT_VISIBLE
        not_visible_shop_product.save()
        lines = [
            {"id": "x", "type": "product", "supplier": {"name": supplier.name, "id": supplier.id}},  # no product?
            {
                "id": "x",
                "type": "product",
                "product": {"id": unshopped_product.id},
                "supplier": {"name": supplier.name, "id": supplier.id},
            },  # not in this shop?
            {
                "id": "y",
                "type": "product",
                "product": {"id": -product.id},
                "supplier": {"name": supplier.name, "id": supplier.id},
            },  # invalid product?
            {
                "id": "z",
                "type": "other",
                "quantity": 1,
                "unitPrice": "q",
                "supplier": {"name": supplier.name, "id": supplier.id},
            },  # what's that price?
            {
                "id": "rr",
                "type": "product",
                "quantity": 1,
                "product": {"id": not_visible_product.id},
                "supplier": {"name": supplier.name, "id": supplier.id},
            },  # not visible
            {"id": "y", "type": "product", "product": {"id": product.id}},  # no supplier
        ]
    state = {
        "customer": {
            "id": contact.id if contact else None,
            "billingAddress": encode_address(contact.default_billing_address) if contact else {},
            "shippingAddress": encode_address(contact.default_shipping_address) if contact else {},
        },
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
                "priceIncludeTaxes": shop.prices_include_tax,
            }
        },
    }
    return state


def get_frontend_request_for_command(state, command, user):
    json_data = json.dumps({"state": state})
    return apply_request_middleware(
        RequestFactory().post(
            "/", data=json_data, content_type="application/json; charset=UTF-8", QUERY_STRING="command=%s" % command
        ),
        user=user,
        skip_session=True,
    )


def get_order_from_state(state, admin_user):
    request = get_frontend_request_for_command(state, "finalize", admin_user)
    response = OrderEditView.as_view()(request)
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

    supplier = get_default_supplier()

    for line in order.lines.all():
        if line.type == OrderLineType.PRODUCT:
            # Check that product line have right taxes
            assert [line_tax.tax.code for line_tax in line.taxes.all()] == ["test_code"]
            assert line.taxful_price.amount > line.taxless_price.amount

        if line.type not in {OrderLineType.PAYMENT, OrderLineType.SHIPPING}:
            # Check that all of the lines that a supplier set, kept it.
            assert line.supplier == supplier


def test_order_creator_invalid_base_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    state = get_frontend_order_state(contact=None)
    # Remove some critical data...
    state["customer"]["id"] = None
    state["shop"]["selected"]["id"] = None
    request = get_frontend_request_for_command(state, "finalize", admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "errorMessage", status_code=400)


def test_order_creator_addresses(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    state = get_frontend_order_state(contact=contact)

    # company with no tax number
    state["customer"]["isCompany"] = True
    request = get_frontend_request_for_command(state, "finalize", admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "Tax number is not set", status_code=400)

    # company with tax number, should work
    state["customer"]["billingAddress"]["tax_number"] = "123"
    state["customer"]["shippingAddress"]["tax_number"] = "123"
    order = get_order_from_state(state, admin_user)
    assert order.lines.count() == 5

    # person with no shipping address
    state["customer"]["isCompany"] = False
    state["customer"]["shippingAddress"] = {}
    request = get_frontend_request_for_command(state, "finalize", admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "This field is required", status_code=400)

    # ship to billing, should work now
    state["customer"]["shipToBillingAddress"] = True
    order = get_order_from_state(state, admin_user)
    assert order.lines.count() == 5

    # change name and make sure contact address is NOT updated
    original_name = contact.default_billing_address.name
    state["customer"]["billingAddress"]["name"] = "foobar"
    state["customer"]["saveAddress"] = False
    order = get_order_from_state(state, admin_user)
    contact.refresh_from_db()
    assert contact.default_billing_address.name == original_name

    # change name with saveAddress set, contact address should update
    original_name = contact.default_billing_address.name
    state["customer"]["billingAddress"]["name"] = "foobar"
    state["customer"]["saveAddress"] = True
    order = get_order_from_state(state, admin_user)
    contact.refresh_from_db()
    assert contact.default_billing_address.name == "foobar"


def test_order_creator_invalid_line_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    state = get_frontend_order_state(contact=contact, valid_lines=False)
    request = get_frontend_request_for_command(state, "finalize", admin_user)
    response = OrderEditView.as_view()(request)
    # Let's see that we get a cornucopia of trouble:
    assert_contains(response, "does not exist", status_code=400)
    assert_contains(response, "does not have a product", status_code=400)
    assert_contains(response, "The price", status_code=400)
    assert_contains(response, "The quantity", status_code=400)
    assert_contains(response, "not have a supplier", status_code=400)


def test_order_creator_view_get(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "shippingMethods")  # in the config
    assert_contains(response, "shops")  # in the config


def test_order_creator_view_invalid_command(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/", {"command": printable_gibberish()}), user=admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "Unknown command", status_code=400)


def test_order_creator_product_data(rf, admin_user):
    shop = get_default_shop()
    product = create_product(sku=printable_gibberish(), supplier=get_default_supplier(), shop=shop)
    request = apply_request_middleware(
        rf.get("/", {"command": "product_data", "shop_id": shop.id, "id": product.id, "quantity": 42}), user=admin_user
    )
    response = OrderEditView.as_view()(request)
    assert_contains(response, "taxClass")
    assert_contains(response, "sku")
    assert_contains(response, product.sku)
    assert_contains(response, "logicalCount")
    assert_contains(response, "physicalCount")
    assert_contains(response, "salesDecimals")
    assert_contains(response, "salesUnit")


def test_order_creator_customer_data(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = apply_request_middleware(rf.get("/", {"command": "customer_data", "id": contact.id}), user=admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "name")
    assert_contains(response, contact.name)


def test_order_creator_source_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = get_frontend_request_for_command(get_frontend_order_state(contact), "source_data", admin_user)
    response = OrderEditView.as_view()(request)
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
        "isCompany": False,
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
        "isCompany": True,
    }
    order = get_order_from_state(state, admin_user)
    assert order.lines.count() == 5
    assert order.customer.id != contact.id
    assert order.customer.name == contact.name
    assert order.customer.tax_number == test_tax_number
    assert order.billing_address.tax_number == contact.default_billing_address.tax_number
    assert order.billing_address.street == contact.default_billing_address.street
    assert order.billing_address.street == order.shipping_address.street


def test_editing_existing_order(rf, admin_user):
    modifier = UserFactory()
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    state = get_frontend_order_state(contact=contact)
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.payment_data = {"payment_data": True}
    order.shipping_data = {"shipping_data": True}
    order.extra_data = {"external_id": "123"}
    order.save()
    assert order.lines.count() == 0
    assert order.pk is not None
    assert order.modified_by == order.creator
    request = get_frontend_request_for_command(state, "finalize", modifier)
    response = OrderEditView.as_view()(request, pk=order.pk)
    assert_contains(response, "orderIdentifier")  # this checks for status codes as a side effect
    data = json.loads(response.content.decode("utf8"))
    edited_order = Order.objects.get(pk=order.pk)  # Re fetch the initial order

    # Check that identifiers has not changed
    assert edited_order.identifier == data["orderIdentifier"] == order.identifier
    assert edited_order.pk == order.pk

    # Check that the product content is updated based on state
    assert edited_order.lines.count() == 5
    assert edited_order.customer == contact

    # Check that product line have right taxes
    for line in edited_order.lines.all():
        if line.type == OrderLineType.PRODUCT:
            assert [line_tax.tax.code for line_tax in line.taxes.all()] == ["test_code"]
            assert line.taxful_price.amount > line.taxless_price.amount

    # Make sure order modification information is correct
    assert edited_order.modified_by != order.modified_by
    assert edited_order.modified_by == modifier
    assert edited_order.modified_on > order.modified_on

    # Make sure all non handled attributes is preserved from original order
    assert edited_order.creator == order.creator
    assert edited_order.ip_address == order.ip_address
    assert edited_order.orderer == order.orderer
    assert edited_order.customer_comment == order.customer_comment
    assert edited_order.marketing_permission == order.marketing_permission
    assert edited_order.order_date == order.order_date
    assert edited_order.status == order.status
    assert edited_order.payment_data == order.payment_data
    assert edited_order.shipping_data == order.shipping_data
    assert edited_order.extra_data == order.extra_data


def test_order_creator_view_for_customer(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = apply_request_middleware(rf.get("/", {"contact_id": contact.id}), user=admin_user)
    response = OrderEditView.as_view()(request)
    assert_contains(response, "customerData")  # in the config
    assert_contains(response, "isCompany")  # in the config


def test_order_creator_customer_details(rf, admin_user):
    shop = get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    company = create_random_company()
    group = get_default_customer_group()
    contact.groups.add(group)
    contact.company_memberships.add(company)
    contact.save()
    product = create_product(sku=printable_gibberish(), supplier=get_default_supplier(), shop=shop)
    order = create_random_order(contact, products=[product])
    request = apply_request_middleware(rf.get("/", {"command": "customer_details", "id": contact.id}), user=admin_user)
    response = OrderEditView.as_view()(request)
    data = json.loads(response.content.decode("utf8"))

    assert "customer_info" in data
    assert "order_summary" in data
    assert "recent_orders" in data
    assert data["customer_info"]["name"] == contact.full_name
    assert data["customer_info"]["phone_no"] == contact.phone
    assert data["customer_info"]["email"] == contact.email
    assert company.full_name in data["customer_info"]["companies"]
    assert group.name in data["customer_info"]["groups"]
    assert data["customer_info"]["merchant_notes"] == contact.merchant_notes
    assert len(data["order_summary"]) == 1
    assert data["order_summary"][0]["year"] == order.order_date.year
    assert data["order_summary"][0]["total"] == format_money(order.taxful_total_price)
    assert len(data["recent_orders"]) == 1
    assert data["recent_orders"][0]["status"] == order.get_status_display()
    assert data["recent_orders"][0]["total"] == format_money(order.taxful_total_price)
    assert data["recent_orders"][0]["payment_status"] == force_text(order.payment_status.label)
    assert data["recent_orders"][0]["shipment_status"] == force_text(order.shipping_status.label)


def test_edit_view_with_anonymous_contact(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku=printable_gibberish(), supplier=supplier, shop=shop)
    order = create_order_with_product(product, supplier, 1, 10, shop=shop)
    order.save()
    assert not order.customer
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = OrderEditView.as_view()(request=request, pk=order.pk)
    assert response.status_code == 200


@pytest.mark.django_db
def test_encode_address():
    contact = create_random_company()
    address = contact.default_billing_address
    address.save()

    assert not address.tax_number

    encoded = encode_address(address)
    for field, value in encoded.items():
        assert getattr(address, field) == value

    # If no tax number, use tax_number argument
    encoded = encode_address(address, tax_number="12345")
    for field, value in encoded.items():
        if field == "tax_number":
            assert value == "12345"
        else:
            assert getattr(address, field) == value

    address.tax_number = "67890"
    address.save()

    # If tax number exists, use existing tax number
    encoded = encode_address(address, tax_number="12345")
    for field, value in encoded.items():
        if field == "tax_number":
            assert value == "67890"
        else:
            assert getattr(address, field) == value
