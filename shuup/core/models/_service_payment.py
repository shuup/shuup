# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import decimal

from django.db import models
from django.http.response import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField
from parler.models import TranslatedFields

from shuup.utils.analog import define_log_model

from ._order_lines import OrderLineType
from ._orders import Order, PaymentStatus
from ._service_base import Service, ServiceChoice, ServiceProvider
from ._service_behavior import StaffOnlyBehaviorComponent


class PaymentMethod(Service):
    payment_processor = models.ForeignKey(
        "PaymentProcessor", null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("payment processor"))

    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_("name"), help_text=_(
                "The payment method name. This name is shown to the customers on checkout."
            )
        ),
        description=models.CharField(
            max_length=500, blank=True, verbose_name=_("description"), help_text=_(
                "The description of the payment method. This description is shown to the customers on checkout."
            )
        ),
    )

    line_type = OrderLineType.PAYMENT
    provider_attr = 'payment_processor'
    shop_product_m2m = "payment_methods"

    class Meta:
        verbose_name = _("payment method")
        verbose_name_plural = _("payment methods")

    def can_delete(self):
        return not Order.objects.filter(payment_method=self).exists()

    def get_payment_process_response(self, order, urls):
        self._make_sure_is_usable()
        return self.provider.get_payment_process_response(self, order, urls)

    def process_payment_return_request(self, order, request):
        self._make_sure_is_usable()
        self.provider.process_payment_return_request(self, order, request)


class PaymentProcessor(ServiceProvider):
    """
    Service provider interface for payment processing.

    Services provided by a payment processor are `payment methods
    <PaymentMethod>`.  To create a new payment method for a payment
    processor, use the `create_service` method.

    Implementers of this interface will provide provide a list of
    payment service choices and each related payment method should have
    one of those service choices assigned to it.

    Payment processing is handled with `get_payment_process_response`
    and `process_payment_return_request` methods.

    Note: `PaymentProcessor` objects should never be created on their
    own but rather through a concrete subclass.
    """

    service_model = PaymentMethod

    def delete(self, *args, **kwargs):
        PaymentMethod.objects.filter(payment_processor=self).update(**{"enabled": False})
        super(PaymentProcessor, self).delete(*args, **kwargs)

    def get_payment_process_response(self, service, order, urls):
        """
        Get payment process response for a given order.

        :type service: shuup.core.models.PaymentMethod
        :type order: shuup.core.models.Order
        :type urls: PaymentUrls
        :rtype: django.http.HttpResponse|None
        """
        return HttpResponseRedirect(urls.return_url)

    def process_payment_return_request(self, service, order, request):
        """
        Process payment return request for a given order.

        Should set ``order.payment_status``.  Default implementation
        just sets it to `~PaymentStatus.DEFERRED` if it is
        `~PaymentStatus.NOT_PAID`.

        :type service: shuup.core.models.PaymentMethod
        :type order: shuup.core.models.Order
        :type request: django.http.HttpRequest
        :rtype: None
        """
        if order.payment_status == PaymentStatus.NOT_PAID:
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Info! Payment status set to `deferred` by %s." % self)
            order.save(update_fields=("payment_status",))

    def _create_service(self, choice_identifier, **kwargs):
        labels = kwargs.pop("labels", None)
        service = PaymentMethod.objects.create(
            payment_processor=self, choice_identifier=choice_identifier, **kwargs)
        if labels:
            service.labels.set(labels)
        return service


class PaymentUrls(object):
    """
    Container for URLs used in payment processing.
    """
    def __init__(self, payment_url, return_url, cancel_url):
        self.payment_url = payment_url
        self.return_url = return_url
        self.cancel_url = cancel_url


class RoundingMode(Enum):
    ROUND_HALF_UP = decimal.ROUND_HALF_UP
    ROUND_HALF_DOWN = decimal.ROUND_HALF_DOWN
    ROUND_UP = decimal.ROUND_UP
    ROUND_DOWN = decimal.ROUND_DOWN

    class Labels:
        ROUND_HALF_UP = _("round up to the nearest number with ties going up, away from zero")
        ROUND_HALF_DOWN = _("round to the nearest number with ties going down, towards zero")
        ROUND_UP = _("round up, away from zero, towards the farther round number")
        ROUND_DOWN = _("round down, towards zero, towards the closest round number")


class CustomPaymentProcessor(PaymentProcessor):
    """
    Payment processor without any integration or special processing.

    Can be used for payment methods whose payments are processed
    manually or generally outside the Shuup.
    """

    rounding_quantize = models.DecimalField(
        max_digits=36, decimal_places=9, default=decimal.Decimal('0.05'), verbose_name=_("rounding quantize"),
        help_text=_("Choose rounding quantize (precision) for cash payment."))
    rounding_mode = EnumField(
        RoundingMode, max_length=50, default=RoundingMode.ROUND_HALF_UP, verbose_name=_("rounding mode"),
        help_text=_("Choose rounding mode for cash payment."))

    class Meta:
        verbose_name = _("custom payment processor")
        verbose_name_plural = _("custom payment processors")

    def get_service_choices(self):
        return [
            ServiceChoice('manual', _("Manually processed payment")),
            ServiceChoice('cash', _("Cash payment"))
        ]

    def _create_service(self, choice_identifier, **kwargs):
        service = super(CustomPaymentProcessor, self)._create_service(
            choice_identifier, **kwargs)
        if choice_identifier == 'cash':
            service.behavior_components.add(
                StaffOnlyBehaviorComponent.objects.create())
        return service

    def process_payment_return_request(self, service, order, request):
        if service == 'cash':
            if not order.is_paid():
                order.create_payment(
                    order.taxful_total_price,
                    payment_identifier="Cash-%s" % now().isoformat(),
                    description="Cash Payment"
                )


PaymentMethodLogEntry = define_log_model(PaymentMethod)
PaymentProcessorLogEntry = define_log_model(PaymentProcessor)
