# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.core.models import (
    CustomCarrier, CustomPaymentProcessor, PaymentStatus
)


class CarrierWithCheckoutPhase(CustomCarrier):
    pass


class PaymentWithCheckoutPhase(CustomPaymentProcessor):
    def process_payment_return_request(self, service, order, request):
        if order.payment_status == PaymentStatus.NOT_PAID and order.payment_data.get("input_value"):
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Customer promised to pay his bills.")
            order.save(update_fields=("payment_status",))
