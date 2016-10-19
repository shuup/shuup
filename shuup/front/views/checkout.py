# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import View
from six.moves import urllib

from shuup.front.checkout import CheckoutProcess, VerticalCheckoutProcess
from shuup.utils.importing import cached_load

__all__ = ["BaseCheckoutView"]


class BaseCheckoutView(View):
    phase_specs = []
    empty_phase_spec = None
    initial_phase = None
    process_class = CheckoutProcess

    def dispatch(self, request, *args, **kwargs):
        if request.basket.is_empty and self.empty_phase_spec:
            self.phase_specs = [self.empty_phase_spec]
            phase_identifier = "empty"
        else:
            phase_identifier = kwargs.get("phase", self.initial_phase)

        process = self.process_class(
            phase_specs=self.phase_specs,
            phase_kwargs=dict(request=self.request, args=self.args, kwargs=self.kwargs)
        )
        if phase_identifier == "reset":
            process.reset()
            return redirect("shuup:checkout")

        current_phase = process.prepare_current_phase(phase_identifier)
        if not current_phase.final and current_phase.identifier != phase_identifier:
            url = reverse("shuup:checkout", kwargs={"phase": current_phase.identifier})
            params = ("?" + urllib.parse.urlencode(request.GET)) if request.GET else ""
            return redirect(url + params)
        return current_phase.dispatch(request, *args, **kwargs)


class DefaultCheckoutView(BaseCheckoutView):
    phase_specs = [
        "shuup.front.checkout.addresses:AddressesPhase",
        "shuup.front.checkout.methods:MethodsPhase",
        "shuup.front.checkout.methods:ShippingMethodPhase",
        "shuup.front.checkout.methods:PaymentMethodPhase",
        "shuup.front.checkout.confirm:ConfirmPhase",
    ]
    empty_phase_spec = "shuup.front.checkout.empty:EmptyPhase"


class SinglePageCheckoutView(DefaultCheckoutView):
    initial_phase = "addresses"
    process_class = VerticalCheckoutProcess


def get_checkout_view():
    view = cached_load("SHUUP_CHECKOUT_VIEW_SPEC")
    if hasattr(view, "as_view"):  # pragma: no branch
        view = view.as_view()
    return view
