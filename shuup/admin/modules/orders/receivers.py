# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.timezone import now

from shuup.core.models import CustomPaymentProcessor


# TEMPORARY until we get admin orders also calling service methods


def _create_cash_payment_for_order(order):
    if not order.is_paid():
        order.create_payment(
            order.taxful_total_price,
            payment_identifier="Cash-%s" % now().isoformat(),
            description="Cash Payment"
        )


def handle_custom_payment_return_requests(sender, order, *args, **kwargs):
    payment_processor = order.payment_method.payment_processor if order.payment_method else None
    if isinstance(payment_processor, CustomPaymentProcessor):
        service = order.payment_method.choice_identifier
        if service == "cash":
            _create_cash_payment_for_order(order)
