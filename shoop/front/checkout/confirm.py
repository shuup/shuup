# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shoop.core.models import OrderStatus
from shoop.front.basket import get_basket_order_creator
from shoop.front.basket.objects import BaseBasket
from shoop.front.checkout import CheckoutPhaseViewMixin


class ConfirmForm(forms.Form):
    accept_terms = forms.BooleanField(required=True, label=_(u"I accept the terms and conditions"))
    marketing = forms.BooleanField(required=False, label=_(u"I want to subscribe to your newsletter"), initial=True)
    comment = forms.CharField(widget=forms.Textarea(), required=False, label=_(u"Comment"))


class ConfirmPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "confirm"
    title = _("Confirmation")

    template_name = "shoop/front/checkout/confirm.jinja"
    form_class = ConfirmForm

    def process(self):
        self.request.basket.customer_comment = self.storage.get("comment")
        self.request.basket.marketing_permission = self.storage.get("marketing")

    def is_valid(self):
        return bool(self.storage.get("accept_terms"))

    def get_context_data(self, **kwargs):
        context = super(ConfirmPhase, self).get_context_data(**kwargs)
        basket = self.request.basket
        assert isinstance(basket, BaseBasket)
        basket.calculate_taxes()
        errors = list(basket.get_validation_errors())
        context["basket"] = basket
        context["errors"] = errors
        context["orderable"] = (not errors)
        return context

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            self.storage[key] = value
        self.process()
        order = self.create_order()
        self.checkout_process.complete()  # Inform the checkout process it's completed

        if order.require_verification:
            return redirect("shoop:order_requires_verification", pk=order.pk, key=order.key)
        else:
            return redirect("shoop:order_process_payment", pk=order.pk, key=order.key)

    def create_order(self):
        basket = self.request.basket
        assert isinstance(basket, BaseBasket)
        assert basket.shop == self.request.shop
        basket.orderer = self.request.person
        basket.customer = self.request.customer
        basket.creator = self.request.user
        basket.status = OrderStatus.objects.get_default_initial()
        order_creator = get_basket_order_creator(request=self.request)
        order = order_creator.create_order(basket)
        basket.finalize()
        return order
