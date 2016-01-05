# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hmac

from django import forms
from django.contrib import messages
from django.http.response import HttpResponse
from django.utils.timezone import now
from django.views.generic import View

from shoop.core.methods.base import BasePaymentMethodModule
from shoop.utils.excs import Problem


HTML_TEMPLATE = u"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>body{background:%(bg_color)s;color:%(fg_color)s;}</style>
</head>
<body>
    <h1>Shoop Pseudo Payment Service</h1>
    <ul>
    %(urls)s
    </li>
</body>
</html>
""".strip()


class ExampleDetailViewClass(View):
    def dispatch(self, request, *args, **kwargs):
        return HttpResponse(
            """
            <div style="margin:auto;text-align:center;margin-top:2em;width:24em;font:24pt comic sans ms,fantasy">
            This blank view could be used for more detailed editing of the module's properties.
            </div>
            """)


class PseudoPaymentMethodModule(BasePaymentMethodModule):
    identifier = "pseudo_payment"
    name = "Shoop Pseudo Payment"
    admin_detail_view_class = ExampleDetailViewClass
    option_fields = BasePaymentMethodModule.option_fields + [
        ("bg_color", forms.CharField(label="Payment Page Background Color", required=False, initial="white")),
        ("fg_color", forms.CharField(label="Payment Page Text Color", required=False, initial="black"))
    ]

    def compute_pseudo_mac(self, order):
        return hmac.new(key=b"PseudoPayment", msg=order.key.encode("utf-8")).hexdigest()

    def get_payment_process_response(self, order, urls):
        mac = self.compute_pseudo_mac(order)
        options = self.get_options()
        html = HTML_TEMPLATE % {
            "urls": "\n".join(
                "<li><a href=\"%s?mac=%s\">%s</a></li>" % (url, mac, title)
                for (title, url) in sorted(urls.items())),
            "bg_color": options.get("bg_color", "white"),
            "fg_color": options.get("fg_color", "black")
        }

        return HttpResponse(html)

    def process_payment_return_request(self, order, request):
        mac = self.compute_pseudo_mac(order)
        if request.REQUEST.get("mac") != mac:
            raise Problem(u"Invalid MAC.")
        if not order.is_paid():
            order.create_payment(
                order.taxful_total_price,
                payment_identifier="Pseudo-%s" % now().isoformat(),
                description="Shoop Pseudo Payment Service Payment"
            )
            messages.success(request, u"Pseudo Payment successfully processed the request.")
