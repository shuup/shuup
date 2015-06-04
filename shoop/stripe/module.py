# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from shoop.core.methods.base import BasePaymentMethodModule
from shoop.stripe.checkout_phase import StripeCheckoutPhase
from shoop.stripe.utils import get_amount_info
from shoop.utils.excs import Problem
from shoop.utils.http import retry_request


class StripeCharger(object):
    def __init__(self, secret_key, order):
        self.secret_key = secret_key
        self.order = order

    def _send_request(self):
        stripe_token = self.order.payment_data["stripe"]["token"]
        input_data = {
            "source": stripe_token,
            "description": "Payment for %s self.order %s" % (self.order.shop, self.order.identifier),
        }
        input_data.update(get_amount_info(self.order.taxful_total_price))

        return retry_request(
            method="post",
            url="https://api.stripe.com/v1/charges",
            data=input_data,
            auth=(self.secret_key, "x"),
            headers={
                "Idempotency-Key": self.order.key,
                "Stripe-Version": "2015-04-07"
            }
        )

    def create_charge(self):
        resp = self._send_request()
        charge_data = resp.json()
        if charge_data.get("error"):
            raise Problem("Stripe: %(message)s (%(type)s)" % charge_data.get("error"))
        if charge_data.get("failure_code") or charge_data.get("failure_message"):
            raise Problem("Stripe: %(failure_message)s (%(failure_code)s)" % charge_data)
        if not charge_data.get("paid"):
            raise Problem("Stripe Charge does not say 'paid'")

        return self.order.create_payment(
            self.order.taxful_total_price,
            payment_identifier="Stripe-%s" % charge_data["id"],
            description="Stripe Charge"
        )


class StripeCheckoutModule(BasePaymentMethodModule):
    identifier = "stripe"
    name = "Stripe Checkout"
    option_fields = BasePaymentMethodModule.option_fields + [
        ("secret_key",
         forms.CharField(label="Secret Key", required=True, widget=forms.PasswordInput(render_value=True))),
        ("publishable_key",
         forms.CharField(label="Publishable Key", required=True, widget=forms.PasswordInput(render_value=True))),
    ]
    checkout_phase_class = StripeCheckoutPhase

    def process_payment_return_request(self, order, request):
        if not order.is_paid():
            charger = StripeCharger(order=order, secret_key=self.get_options()["secret_key"])
            charger.create_charge()
