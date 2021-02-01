# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hmac

from django.contrib import messages
from django.db import models
from django.http.response import HttpResponse
from django.utils.timezone import now

from shuup.core.models import (
    FixedCostBehaviorComponent, PaymentProcessor, ServiceChoice,
    WaivingCostBehaviorComponent
)
from shuup.utils.excs import Problem

HTML_TEMPLATE = u"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>body{background:%(bg_color)s;color:%(fg_color)s;}</style>
</head>
<body>
    <h1>%(title)s</h1>
    <ul>
    %(urls)s
    </li>
</body>
</html>
""".strip()


class PseudoPaymentProcessor(PaymentProcessor):
    bg_color = models.CharField(
        max_length=20, blank=True, default="white",
        verbose_name="Payment Page Background Color")
    fg_color = models.CharField(
        max_length=20, blank=True, default="black",
        verbose_name="Payment Page Text Color")

    def get_service_choices(self):
        return [
            ServiceChoice('normal', "Pseudo payment"),
            ServiceChoice('caps', "Pseudo payment CAPS"),
        ]

    def _create_service(self, choice_identifier, **kwargs):
        service = super(PseudoPaymentProcessor, self)._create_service(
            choice_identifier, **kwargs)
        service.behavior_components.add(
            WaivingCostBehaviorComponent.objects.create(
                price_value=10, waive_limit_value=1000))
        if choice_identifier == 'caps':
            service.behavior_components.add(
                FixedCostBehaviorComponent.objects.create(
                    price_value=50, description="UPPERCASING EXTRA FEE"))
        return service

    def compute_pseudo_mac(self, order):
        return hmac.new(key=b"PseudoPayment", msg=order.key.encode("utf-8")).hexdigest()

    def get_payment_process_response(self, service, order, urls):
        transform = self._get_text_transformer(service)
        mac = self.compute_pseudo_mac(order)
        url_list = [
            ("Pay", urls.payment_url),
            ("Cancel payment", urls.cancel_url),
            ("Return", urls.return_url),
        ]
        urls_html = "\n".join(
            "<li><a href=\"%s?mac=%s\">%s</a></li>" % (
                url, mac, transform(title))
            for (title, url) in url_list)
        html = HTML_TEMPLATE % {
            "urls": urls_html,
            "title": transform("Shuup Pseudo Payment Service"),
            "bg_color": self.bg_color or "white",
            "fg_color": self.fg_color or "black",
        }

        return HttpResponse(html)

    def process_payment_return_request(self, service, order, request):
        transform = self._get_text_transformer(service)
        mac = self.compute_pseudo_mac(order)
        if request.GET.get("mac") != mac:
            raise Problem(u"Error! Invalid MAC.")
        if not order.is_paid():
            order.create_payment(
                order.taxful_total_price,
                payment_identifier="Pseudo-%s" % now().isoformat(),
                description=transform("Shuup Pseudo Payment Service Payment")
            )
            msg = transform(
                "Success! The request was processed by Pseudo Payment.")
            messages.success(request, msg)

    def _get_text_transformer(self, service):
        choice = service.choice_identifier
        if choice == 'caps':
            return type("").upper
        elif choice == 'normal':
            return type("")
        else:
            raise ValueError('Error! Invalid service choice: `%r`.' % choice)
