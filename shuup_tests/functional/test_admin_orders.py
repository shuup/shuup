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
from django.core import serializers
from django.utils.translation import activate

from shuup.core.models import CustomPaymentProcessor, PaymentMethod, RoundingMode, ShopProductVisibility, Tax, TaxClass
from shuup.default_tax.models import TaxRule
from shuup.testing.factories import (
    create_product,
    create_random_person,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
    get_initial_order_status,
)
from shuup_tests.admin.test_order_creator import get_order_from_state
from shuup_tests.utils import printable_gibberish


def encode_address(address):
    return json.loads(serializers.serialize("json", [address]))[0].get("fields")


@pytest.mark.django_db
def get_frontend_order_state(contact, payment_method, product_price, valid_lines=True):
    """
    Get a dict structure mirroring what the frontend JavaScript would submit.
    :type contact: Contact|None
    """
    activate("en")
    shop = get_default_shop()
    tax = Tax.objects.create(code="test_code", rate=decimal.Decimal("0.20"), name="Default")
    tax_class = TaxClass.objects.create(identifier="test_tax_class", name="Default")
    rule = TaxRule.objects.create(tax=tax)
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
                "quantity": "1",
                "baseUnitPrice": product_price,
                "supplier": {"name": supplier.name, "id": supplier.id},
            },
            {"id": "z", "type": "text", "text": "This was an order!", "quantity": 0},
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
            "paymentMethod": {"id": payment_method.id},
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "price, target, mode",
    [
        ("2.32", "2.30", RoundingMode.ROUND_DOWN),
        ("2.35", "2.35", RoundingMode.ROUND_DOWN),
        ("2.38", "2.35", RoundingMode.ROUND_DOWN),
        ("2.32", "2.35", RoundingMode.ROUND_UP),
        ("2.35", "2.35", RoundingMode.ROUND_UP),
        ("2.38", "2.40", RoundingMode.ROUND_UP),
        ("2.32", "2.30", RoundingMode.ROUND_HALF_DOWN),
        ("2.35", "2.35", RoundingMode.ROUND_HALF_DOWN),
        ("2.38", "2.40", RoundingMode.ROUND_HALF_DOWN),
        ("2.32", "2.30", RoundingMode.ROUND_HALF_UP),
        ("2.35", "2.35", RoundingMode.ROUND_HALF_UP),
        ("2.38", "2.40", RoundingMode.ROUND_HALF_UP),
    ],
)
def test_admin_cash_order(rf, admin_user, price, target, mode):
    activate("en")
    get_initial_order_status()  # Needed for the API
    shop = get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    processor = CustomPaymentProcessor.objects.create(rounding_mode=mode)
    cash_method = PaymentMethod.objects.create(
        shop=shop, payment_processor=processor, choice_identifier="cash", tax_class=get_default_tax_class(), name="Cash"
    )

    state = get_frontend_order_state(contact, cash_method, price)
    order = get_order_from_state(state, admin_user)
    assert order.payment_method == cash_method
    assert order.lines.count() == 5  # 2 submitted, two for the shipping and payment method, and a rounding line
    assert order.creator == admin_user
    assert order.customer == contact
    assert order.taxful_total_price == shop.create_price(target)
