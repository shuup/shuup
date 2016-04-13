# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.core.models import CustomPaymentProcessor, PaymentStatus
from shoop.testing.simple_checkout_phase import TestCheckoutPhase


class PaymentWithCheckoutPhase(CustomPaymentProcessor):
    checkout_phase_class = TestCheckoutPhase

    def process_payment_return_request(self, service, order, request):
        if order.payment_status == PaymentStatus.NOT_PAID and order.payment_data.get("promised_to_pay"):
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Customer promised to pay his bills.")
            order.save(update_fields=("payment_status",))
