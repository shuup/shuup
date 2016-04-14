# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from django.db import models
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from ._order_lines import OrderLineType
from ._orders import PaymentStatus
from ._service_base import Service, ServiceChoice, ServiceProvider


class PaymentMethod(Service):
    payment_processor = models.ForeignKey(
        "PaymentProcessor", null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("payment processor"))

    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_("name")),
        description=models.CharField(
            max_length=500, blank=True, verbose_name=_("description")),
    )

    line_type = OrderLineType.PAYMENT
    provider_attr = 'payment_processor'
    shop_product_m2m = "payment_methods"

    class Meta:
        verbose_name = _("payment method")
        verbose_name_plural = _("payment methods")

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
    def get_payment_process_response(self, service, order, urls):
        """
        Get payment process response for given order.

        :type service: shoop.core.models.PaymentMethod
        :type order: shoop.core.models.Order
        :type urls: PaymentUrls
        :rtype: django.http.HttpResponse|None
        """
        return HttpResponseRedirect(urls.return_url)

    def process_payment_return_request(self, service, order, request):
        """
        Process payment return request for given order.

        Should set ``order.payment_status``.  Default implementation
        just sets it to `~PaymentStatus.DEFERRED` if it is
        `~PaymentStatus.NOT_PAID`.

        :type service: shoop.core.models.PaymentMethod
        :type order: shoop.core.models.Order
        :type request: django.http.HttpRequest
        :rtype: None
        """
        if order.payment_status == PaymentStatus.NOT_PAID:
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Payment status set to deferred by %s" % self)
            order.save(update_fields=("payment_status",))

    def _create_service(self, choice_identifier, **kwargs):
        return PaymentMethod.objects.create(
            payment_processor=self, choice_identifier=choice_identifier, **kwargs)


class PaymentUrls(object):
    """
    Container for URLs used in payment processing.
    """
    def __init__(self, payment_url, return_url, cancel_url):
        self.payment_url = payment_url
        self.return_url = return_url
        self.cancel_url = cancel_url


class CustomPaymentProcessor(PaymentProcessor):
    """
    Payment processor without any integration or special processing.

    Can be used for payment methods whose payments are processed
    manually.
    """
    class Meta:
        verbose_name = _("custom payment processor")
        verbose_name_plural = _("custom payment processors")

    def get_service_choices(self):
        return [ServiceChoice('manual', _("Manually processed payment"))]
