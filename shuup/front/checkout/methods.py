# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging
from collections import defaultdict

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.edit import FormView

from shuup import configuration
from shuup.core.models import PaymentMethod, ShippingMethod
from shuup.front.checkout import CheckoutPhaseViewMixin
from shuup.utils.iterables import first

from ._services import get_checkout_phases_for_service

LOG = logging.getLogger(__name__)

SHIPPING_METHOD_REQUIRED_CONFIG_KEY = "checkout_required_method:shipping"
PAYMENT_METHOD_REQUIRED_CONFIG_KEY = "checkout_required_method:payment"


class MethodWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super(MethodWidget, self).__init__(attrs)
        self.choices = list(choices)
        self.field_name = None
        self.basket = None
        self.request = None

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(
            render_to_string("shuup/front/checkout/method_choice.jinja", {
                "field_name": self.field_name,
                "grouped_methods": _get_methods_grouped_by_service_provider(self.choices),
                "current_value": value,
                "basket": self.basket,
                "request": self.request
            })
        )


def _get_methods_grouped_by_service_provider(methods):
    grouped_methods = defaultdict(list)
    for method in methods:
        grouped_methods[getattr(method, method.provider_attr)].append(method)
    return grouped_methods


class MethodChoiceIterator(forms.models.ModelChoiceIterator):
    def choice(self, obj):
        return obj


class MethodsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.basket = kwargs.pop("basket")
        self.shop = kwargs.pop("shop")
        super(MethodsForm, self).__init__(*args, **kwargs)

        self.fields["shipping_method"] = forms.ModelChoiceField(
            queryset=ShippingMethod.objects.all(),
            widget=MethodWidget(),
            label=_('shipping method'),
            required=configuration.get(self.shop, SHIPPING_METHOD_REQUIRED_CONFIG_KEY, True)
        )
        self.fields["payment_method"] = forms.ModelChoiceField(
            queryset=PaymentMethod.objects.all(),
            widget=MethodWidget(),
            label=_('payment method'),
            required=configuration.get(self.shop, PAYMENT_METHOD_REQUIRED_CONFIG_KEY, True)
        )
        self.limit_method_fields()

    def limit_method_fields(self):
        basket = self.basket  # noqa (F821) type: shuup.front.basket.objects.BaseBasket
        for field_name, methods in (
            ("shipping_method", basket.get_available_shipping_methods()),
            ("payment_method", basket.get_available_payment_methods()),
        ):
            field = self.fields[field_name]
            mci = MethodChoiceIterator(field)
            field.choices = [mci.choice(obj) for obj in methods]
            field.widget.field_name = field_name
            field.widget.basket = self.basket
            field.widget.request = self.request
            if field.choices:
                field.initial = field.choices[0]


class MethodsPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "methods"
    title = _(u"Shipping & Payment")
    template_name = "shuup/front/checkout/methods.jinja"
    form_class = MethodsForm

    def is_valid(self):
        shipping_required = configuration.get(self.request.shop, SHIPPING_METHOD_REQUIRED_CONFIG_KEY, True)
        payment_required = configuration.get(self.request.shop, PAYMENT_METHOD_REQUIRED_CONFIG_KEY, True)

        if shipping_required and not self.storage.get("shipping_method_id"):
            return False
        if payment_required and not self.storage.get("payment_method_id"):
            return False

        return True

    def process(self):
        shipping_method = ShippingMethod.objects.filter(pk=self.storage.get("shipping_method_id")).first()
        payment_method = PaymentMethod.objects.filter(pk=self.storage.get("payment_method_id")).first()

        self.basket.shipping_method_id = shipping_method.pk if shipping_method else None
        self.basket.payment_method_id = payment_method.pk if payment_method else None

    def get_form_kwargs(self):
        kwargs = super(MethodsPhase, self).get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["basket"] = self.basket
        kwargs["shop"] = self.request.shop
        return kwargs

    def form_valid(self, form):
        for field_name in ["shipping_method", "payment_method"]:
            storage_key = "%s_id" % field_name
            value = None

            if form.cleaned_data.get(field_name):
                value = form.cleaned_data[field_name].id

            self.storage[storage_key] = value

        return super(MethodsPhase, self).form_valid(form)

    def get_initial(self):
        initial = {}
        for key in ("shipping_method", "payment_method"):
            value = self.storage.get("%s_id" % key)
            if value:
                initial[key] = value
        return initial

    def get_context_data(self, **kwargs):
        context = super(MethodsPhase, self).get_context_data(**kwargs)
        context["show_shipping"] = self.basket.has_shippable_lines()
        return context


class _MethodDependentCheckoutPhase(CheckoutPhaseViewMixin):
    """
    Wrap the method module's checkout phase.
    """

    def get_method(self):
        """
        :rtype: shuup.core.models.Service
        """
        raise NotImplementedError("Error! Not implemented: `_MethodDependentCheckoutPhase` -> `get_method()`.")

    def get_method_checkout_phase_object(self):
        """
        :rtype: shuup.front.checkout.CheckoutPhaseViewMixin|None
        """
        if hasattr(self, "_checkout_phase_object"):
            return self._checkout_phase_object

        method = self.get_method()
        if not method:
            return None
        phases = get_checkout_phases_for_service(self.checkout_process, method)
        phase = first(phases)
        if not phase:
            return None
        self._checkout_phase_object = phase
        return phase

    def _wrap_method(self, method_name, default_return=True):
        phase_obj = self.get_method_checkout_phase_object()
        if phase_obj:
            return getattr(phase_obj, method_name)()
        return default_return

    def should_skip(self):
        return self._wrap_method("should_skip")

    def is_valid(self):
        return self._wrap_method("is_valid")

    def process(self):
        return self._wrap_method("process")

    def reset(self):
        return self._wrap_method("reset")

    @property
    def title(self):
        phase_obj = self.get_method_checkout_phase_object()
        return (phase_obj.title if phase_obj else "")

    def dispatch(self, request, *args, **kwargs):
        # This should never be called if the object doesn't exist, hence no checks
        phase = self.get_method_checkout_phase_object()
        self.checkout_process.add_phase_attributes(phase, self)
        return phase.dispatch(request, *args, **kwargs)


class ShippingMethodPhase(_MethodDependentCheckoutPhase, View):
    identifier = "shipping"

    def get_method(self):
        return self.basket.shipping_method


class PaymentMethodPhase(_MethodDependentCheckoutPhase, View):
    identifier = "payment"

    def get_method(self):
        return self.basket.payment_method
