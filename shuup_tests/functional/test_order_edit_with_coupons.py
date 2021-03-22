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
from django.core import serializers

from shuup.admin.modules.orders.views.edit import OrderEditView
from shuup.campaigns.models import BasketCampaign, Coupon
from shuup.campaigns.models.basket_conditions import BasketTotalProductAmountCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.core.models import Order, OrderLineType, Tax, TaxClass
from shuup.core.order_creator import OrderCreator
from shuup.default_tax.models import TaxRule
from shuup.front.basket import get_basket
from shuup.testing.factories import (
    UserFactory,
    create_product,
    create_random_person,
    create_random_user,
    get_default_supplier,
    get_initial_order_status,
    get_payment_method,
    get_shipping_method,
)
from shuup_tests.admin.test_order_creator import get_frontend_request_for_command
from shuup_tests.campaigns import initialize_test
from shuup_tests.utils import assert_contains, printable_gibberish


@pytest.mark.django_db
def test_order_edit_with_coupon(rf):
    initial_status = get_initial_order_status()
    request, shop, group = initialize_test(rf, include_tax=False)
    order = _get_order_with_coupon(request, initial_status)

    staff_user = create_random_user(is_staff=True)

    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    assert order.customer != contact
    state = _get_frontend_order_state(shop, contact)
    assert order.shop.id == state["shop"]["selected"]["id"]

    request = get_frontend_request_for_command(state, "finalize", staff_user)
    response = OrderEditView.as_view()(request, pk=order.pk)
    assert_contains(response, "orderIdentifier")
    data = json.loads(response.content.decode("utf8"))
    edited_order = Order.objects.get(pk=order.pk)

    assert edited_order.identifier == data["orderIdentifier"] == order.identifier
    assert edited_order.pk == order.pk
    assert edited_order.lines.count() == 4
    assert OrderLineType.DISCOUNT in [l.type for l in edited_order.lines.all()]
    assert edited_order.coupon_usages.count() == 1


@pytest.mark.django_db
def test_campaign_with_non_active_coupon(rf):
    initial_status = get_initial_order_status()
    request, shop, group = initialize_test(rf, include_tax=False)
    order = _get_order_with_coupon(request, initial_status)
    coupon = order.coupon_usages.first().coupon
    coupon.active = False
    coupon.save()

    modifier = UserFactory()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    assert order.customer != contact
    state = _get_frontend_order_state(shop, contact)
    assert order.shop.id == state["shop"]["selected"]["id"]

    request = get_frontend_request_for_command(state, "finalize", modifier)
    response = OrderEditView.as_view()(request, pk=order.pk)
    assert_contains(response, "orderIdentifier")
    data = json.loads(response.content.decode("utf8"))
    edited_order = Order.objects.get(pk=order.pk)

    assert edited_order.identifier == data["orderIdentifier"] == order.identifier
    assert edited_order.pk == order.pk
    assert edited_order.lines.count() == 3
    assert OrderLineType.DISCOUNT not in [l.type for l in edited_order.lines.all()]
    assert edited_order.coupon_usages.count() == 0


def _get_order_with_coupon(request, initial_status, condition_product_count=1):
    shop = request.shop
    basket = get_basket(request)
    supplier = get_default_supplier(shop)
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)  # For shippable products

    dc = Coupon.objects.create(code="TEST", active=True)
    campaign = BasketCampaign.objects.create(shop=shop, name="test", public_name="test", coupon=dc, active=True)

    BasketDiscountAmount.objects.create(discount_amount=shop.create_price("20"), campaign=campaign)

    rule = BasketTotalProductAmountCondition.objects.create(value=1)
    campaign.conditions.add(rule)
    campaign.save()
    basket.add_code(dc.code)
    basket.save()

    basket.status = initial_status
    creator = OrderCreator(request)
    order = creator.create_order(basket)
    assert order.lines.count() == 3
    assert OrderLineType.DISCOUNT in [l.type for l in order.lines.all()]
    return order


def _encode_address(address):
    return json.loads(serializers.serialize("json", [address]))[0].get("fields")


def _get_frontend_order_state(shop, contact):
    tax = Tax.objects.create(code="test_code", rate=decimal.Decimal("0.20"), name="Default")
    tax_class = TaxClass.objects.create(identifier="test_tax_class", name="Default")
    rule = TaxRule.objects.create(tax=tax)
    rule.tax_classes.add(tax_class)
    rule.save()
    supplier = get_default_supplier(shop)
    product = create_product(sku=printable_gibberish(), supplier=supplier, shop=shop)
    product.tax_class = tax_class
    product.save()
    lines = [
        {
            "id": "x",
            "type": "product",
            "product": {"id": product.id},
            "quantity": "32",
            "baseUnitPrice": 50,
            "supplier": {"name": supplier.name, "id": supplier.id},
        }
    ]

    state = {
        "customer": {
            "id": contact.id if contact else None,
            "billingAddress": _encode_address(contact.default_billing_address) if contact else {},
            "shippingAddress": _encode_address(contact.default_shipping_address) if contact else {},
        },
        "lines": lines,
        "methods": {
            "shippingMethod": {"id": get_shipping_method(shop=shop).id},
            "paymentMethod": {"id": get_payment_method(shop=shop).id},
        },
        "shop": {
            "selected": {
                "id": shop.id,
                "name": shop.safe_translation_getter("name"),
                "currency": shop.currency,
                "priceIncludeTaxes": shop.prices_include_tax,
            }
        },
    }
    return state
