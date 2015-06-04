# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from shoop.front.checkout import CheckoutPhaseViewMixin
from .utils import get_amount_info


class StripeTokenForm(forms.Form):
    # Camel case only as that's what Stripe does
    stripeToken = forms.CharField(widget=forms.HiddenInput, required=True)
    stripeTokenType = forms.CharField(widget=forms.HiddenInput, required=False)
    stripeEmail = forms.CharField(widget=forms.HiddenInput, required=False)


class StripeCheckoutPhase(CheckoutPhaseViewMixin, FormView):
    module = None  # Injected by the method phase
    identifier = "stripe"
    title = "Stripe"
    template_name = "shoop/stripe/checkout_phase.jinja"
    form_class = StripeTokenForm

    def get_stripe_context(self):
        options = self.module.get_options()
        config = {
            "publishable_key": options["publishable_key"],
            "name": force_text(self.request.shop),
            "description": force_text(_("Purchase")),
        }
        config.update(get_amount_info(self.request.basket.total_price))
        return config

    def get_context_data(self, **kwargs):
        context = super(StripeCheckoutPhase, self).get_context_data(**kwargs)
        context["stripe"] = self.get_stripe_context()
        return context

    def is_valid(self):
        return "token" in self.storage.get("stripe", {})

    def form_valid(self, form):
        self.storage["stripe"] = {
            "token": form.cleaned_data.get("stripeToken"),
            "token_type": form.cleaned_data.get("stripeTokenType"),
            "email": form.cleaned_data.get("stripeEmail"),
        }
        return super(StripeCheckoutPhase, self).form_valid(form)

    def process(self):
        self.request.basket.payment_data["stripe"] = self.storage["stripe"]
