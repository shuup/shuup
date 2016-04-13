# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from django.views.generic.edit import FormView

from shoop.front.checkout import CheckoutPhaseViewMixin


class TestCheckoutPhaseForm(forms.Form):
    will_pay = forms.BooleanField(required=True, label="I promise to pay this order")


class TestCheckoutPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "test_payment_phase"
    title = "Test Payment Phase"
    template_name = "shoop_testing/simple_checkout_phase.jinja"
    form_class = TestCheckoutPhaseForm

    def form_valid(self, form):
        self.storage['payment_with_checkout_phase'] = {
            'will_pay': form.cleaned_data.get('will_pay'),
        }
        return super(TestCheckoutPhase, self).form_valid(form)

    def is_valid(self):
        data = self.storage.get('payment_with_checkout_phase', {})
        return bool(data.get('will_pay'))

    def process(self):
        data = self.storage.get('payment_with_checkout_phase', {})
        self.request.basket.payment_data["promised_to_pay"] = data.get('will_pay')
