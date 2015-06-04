# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.timezone import now
import os

import pytest
from shoop.stripe.module import StripeCheckoutModule
from shoop.testing.factories import get_default_product, get_default_supplier, create_order_with_product
from shoop.utils.http import retry_request


@pytest.mark.django_db
def test_stripe(rf):
    sk = os.environ.get("STRIPE_SECRET_KEY")
    if not sk:
        pytest.skip("Can't test Stripe without STRIPE_SECRET_KEY envvar")

    order = _create_order_for_stripe()

    resp = retry_request(
        method="post",
        url="https://api.stripe.com/v1/tokens",
        auth=(sk, "x"),
        data={
            "card[number]": "4242424242424242",
            "card[exp_month]": 12,
            "card[exp_year]": now().date().year + 1,
            "card[cvc]": 666,
        }
    )
    token_id = resp.json()["id"]
    spm = StripeCheckoutModule(None, {"publishable_key": "x", "secret_key": sk})
    order.payment_data["stripe"] = {"token": token_id}
    order.save()
    spm.process_payment_return_request(order, rf.post("/"))
    assert order.is_paid()
    assert order.payments.first().payment_identifier.startswith("Stripe-")


def _create_order_for_stripe():
    product = get_default_product()
    supplier = get_default_supplier()
    order = create_order_with_product(product, supplier=supplier, quantity=1, taxless_unit_price=100, tax_rate=0)
    order.cache_prices()
    assert order.taxless_total_price > 0
    if not order.payment_data:
        order.payment_data = {}
    order.save()
    return order
