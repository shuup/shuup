# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import View
from six.moves import urllib

from shoop.front.checkout import CheckoutProcess
from shoop.utils.importing import cached_load

__all__ = ["BaseCheckoutView"]


class BaseCheckoutView(View):
    phase_specs = []
    empty_phase_spec = None

    def dispatch(self, request, *args, **kwargs):
        if request.basket.is_empty and self.empty_phase_spec:
            self.phase_specs = [self.empty_phase_spec]

        process = CheckoutProcess(
            phase_specs=self.phase_specs,
            phase_kwargs=dict(request=self.request, args=self.args, kwargs=self.kwargs)
        )
        phase_identifier = kwargs.get("phase")
        if phase_identifier == "reset":
            process.reset()
            return redirect("shoop:checkout")

        current_phase = process.prepare_current_phase(phase_identifier)
        if not current_phase.final and current_phase.identifier != phase_identifier:
            url = reverse("shoop:checkout", kwargs={"phase": current_phase.identifier})
            params = ("?" + urllib.parse.urlencode(request.GET)) if request.GET else ""
            return redirect(url + params)
        return current_phase.dispatch(request, *args, **kwargs)


class DefaultCheckoutView(BaseCheckoutView):
    phase_specs = [
        "shoop.front.checkout.addresses:AddressesPhase",
        "shoop.front.checkout.methods:MethodsPhase",
        "shoop.front.checkout.methods:ShippingMethodPhase",
        "shoop.front.checkout.methods:PaymentMethodPhase",
        "shoop.front.checkout.confirm:ConfirmPhase",
    ]
    empty_phase_spec = "shoop.front.checkout.empty:EmptyPhase"


class SinglePhaseCheckoutView(BaseCheckoutView):
    phase_specs = [
        "shoop.front.checkout.single_page.SingleCheckoutPhase"
    ]
    empty_phase_spec = None  # Use the same phase specs when the basket is empty


def get_checkout_view():
    view = cached_load("SHOOP_CHECKOUT_VIEW_SPEC")
    if hasattr(view, "as_view"):  # pragma: no branch
        view = view.as_view()
    return view
