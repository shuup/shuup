# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from shoop.core.models import Order
from shoop.front.signals import order_complete_viewed


class OrderCompleteView(DetailView):
    template_name = "shoop/front/order/complete.jinja"
    model = Order
    context_object_name = "order"

    def render_to_response(self, context, **response_kwargs):
        order_complete_viewed.send(sender=self, order=self.object, request=self.request)
        return super(OrderCompleteView, self).render_to_response(context, **response_kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs["pk"], key=self.kwargs["key"])


class OrderRequiresVerificationView(DetailView):
    template_name = "shoop/front/order/requires_verification.jinja"
    model = Order

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs["pk"], key=self.kwargs["key"])

    def get_context_data(self, **kwargs):
        context = super(OrderRequiresVerificationView, self).get_context_data(**kwargs)
        if self.object.user and self.object.user.password == "//IMPLICIT//":
            from shoop.shop.views.activation_views import OneShotActivationForm
            context["activation_form"] = OneShotActivationForm()
        return context

    def get(self, request, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
