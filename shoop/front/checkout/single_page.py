# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shoop.core.models import (
    CompanyContact, MutableAddress, OrderStatus, PaymentMethod, ShippingMethod
)
from shoop.front.basket import get_basket_order_creator
from shoop.front.basket.objects import BaseBasket
from shoop.front.checkout import CheckoutPhaseViewMixin
from shoop.utils.fields import RelaxedModelChoiceField
from shoop.utils.form_group import FormGroup

from ._mixins import TaxNumberCleanMixin


class AddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = ("name", "phone", "email", "street", "street2", "postal_code", "city", "region", "country")

    def __init__(self, **kwargs):
        super(AddressForm, self).__init__(**kwargs)
        if not kwargs.get("instance"):
            # Set default country
            self.fields["country"].initial = settings.SHOOP_ADDRESS_HOME_COUNTRY


def _to_choices(objects):
    return [(x.id, x) for x in objects]


class OrderForm(TaxNumberCleanMixin, forms.Form):
    company_name = forms.CharField(max_length=128, required=False, label=_(u"Company name"))
    tax_number = forms.CharField(max_length=32, required=False, label=_("Tax number"))
    shipping_method = RelaxedModelChoiceField(queryset=ShippingMethod.objects.none(), label=_(u"Shipping method"))
    payment_method = RelaxedModelChoiceField(queryset=PaymentMethod.objects.none(), label=_(u"Payment method"))
    accept_terms = forms.BooleanField(required=True, label=_(u"I accept the terms and conditions"))
    marketing = forms.BooleanField(required=False, label=_(u"Please send me marketing correspondence"))
    comment = forms.CharField(widget=forms.Textarea(), required=False, label=_("Comment"))

    def __init__(self, *args, **kwargs):
        self.basket = kwargs.pop("basket")
        self.shop = kwargs.pop("shop")
        super(OrderForm, self).__init__(*args, **kwargs)
        self.limit_method_fields()

    def limit_method_fields(self):
        basket = self.basket  # type: shoop.front.basket.objects.BaseBasket
        shipping_methods = basket.get_available_shipping_methods()
        payment_methods = basket.get_available_payment_methods()
        self["shipping_method"].field.choices = _to_choices(shipping_methods)
        self["payment_method"].field.choices = _to_choices(payment_methods)


class SingleCheckoutPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "checkout"
    final = True
    template_name = "shoop/front/checkout/single_phase.jinja"
    billing_address_form_class = AddressForm
    shipping_address_form_class = AddressForm
    order_form_class = OrderForm

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        fg = FormGroup(data=kwargs.get("data"), files=kwargs.get("files"))
        fg.add_form_def("billing", self.billing_address_form_class)
        fg.add_form_def("shipping", self.shipping_address_form_class)
        fg.add_form_def("order", self.order_form_class, kwargs={
            "basket": self.request.basket,
            "shop": self.request.shop
        })
        return fg

    def get_context_data(self, **kwargs):
        ctx = FormView.get_context_data(self, **kwargs)
        basket = self.request.basket  # type: shoop.front.basket.objects.BaseBasket
        ctx["basket"] = basket
        basket.calculate_taxes()
        errors = list(basket.get_validation_errors())
        ctx["errors"] = errors
        ctx["orderable"] = (not errors)
        return ctx

    def form_valid(self, form):
        basket = self.request.basket
        assert isinstance(basket, BaseBasket)
        order_data = form["order"].cleaned_data.copy()
        if not order_data.pop("accept_terms", None):  # pragma: no cover
            raise ValidationError("Terms must be accepted")

        basket.shop = self.request.shop
        basket.orderer = self.request.person
        basket.customer = self.request.customer
        basket.shipping_address = form["shipping"].save(commit=False)
        basket.billing_address = form["billing"].save(commit=False)
        basket.shipping_method = order_data.pop("shipping_method")
        basket.payment_method = order_data.pop("payment_method")
        basket.status = OrderStatus.objects.get_default_initial()
        company_name = order_data.pop("company_name")
        tax_number = order_data.pop("tax_number")
        if company_name and tax_number:
            # Not using `get_or_create` here because duplicates are better than accidental information leakage
            basket.customer = CompanyContact.objects.create(name=company_name, tax_number=tax_number)
            for address in (basket.shipping_address, basket.billing_address):
                address.company_name = basket.customer.name
                address.tax_number = basket.customer.tax_number
        basket.marketing_permission = order_data.pop("marketing")
        basket.customer_comment = order_data.pop("comment")

        if order_data:  # pragma: no cover
            raise ValueError("`order_data` should be empty by now")

        order_creator = get_basket_order_creator(request=self.request)
        order = order_creator.create_order(basket)
        basket.finalize()
        self.checkout_process.complete()

        if order.require_verification:
            return redirect("shoop:order_requires_verification", pk=order.pk, key=order.key)
        else:
            return redirect("shoop:order_process_payment", pk=order.pk, key=order.key)

    def process(self):
        pass
