# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView

from shuup.core.models import Order, PaymentUrls
from shuup.utils.django_compat import reverse


def get_payment_urls(request, order):
    """
    :type request: django.http.HttpRequest
    """
    kwargs = dict(pk=order.pk, key=order.key)

    def absolute_url_for(name):
        return request.build_absolute_uri(reverse(name, kwargs=kwargs))

    return PaymentUrls(
        payment_url=absolute_url_for("shuup:order_process_payment"),
        return_url=absolute_url_for("shuup:order_process_payment_return"),
        cancel_url=absolute_url_for("shuup:order_payment_canceled"),
    )


class ProcessPaymentView(DetailView):
    model = Order
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs["pk"], key=self.kwargs["key"])

    def get_context_data(self, **kwargs):
        context = super(ProcessPaymentView, self).get_context_data(**kwargs)
        context["payment_urls"] = get_payment_urls(self.request, self.object)
        return context

    def dispatch(self, request, *args, **kwargs):
        mode = self.kwargs["mode"]
        order = self.object = self.get_object()
        payment_method = (order.payment_method if order.payment_method_id else None)
        if mode == "payment":
            if not order.is_paid():
                if payment_method:
                    return payment_method.get_payment_process_response(
                        order=order, urls=get_payment_urls(request, order))
        elif mode == "return":
            if payment_method:
                payment_method.process_payment_return_request(order=order, request=request)
        elif mode == "cancel":
            self.template_name = "shuup/front/order/payment_canceled.jinja"
            return self.render_to_response(self.get_context_data(object=order))
        else:
            raise ImproperlyConfigured("Error! Unknown ProcessPaymentView mode: `%s`." % mode)

        return redirect("shuup:order_complete", pk=order.pk, key=order.key)
