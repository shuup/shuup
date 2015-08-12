# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from shoop.core.models import Address
from shoop.core.models.contacts import CompanyContact
from shoop.core.utils.vat import verify_vat
from shoop.front.checkout import CheckoutPhaseViewMixin
from shoop.utils.form_group import FormGroup


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("name", "phone", "email", "street", "street2", "postal_code", "city", "region", "country")


class CompanyForm(forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = ("name", "vat_code",)

    def clean_vat_code(self):
        vat_code = self.cleaned_data["vat_code"].strip()
        if vat_code:
            prefix, parts = verify_vat(vat_code, "FI")  # TODO: 'fi' isn't the best default
            if not vat_code.startswith(prefix):
                vat_code = prefix + vat_code  # Always add prefix
        return vat_code

    def clean(self):
        company_name = self.cleaned_data.get("name")
        vat_code = self.cleaned_data.get("vat_code")
        if bool(company_name) ^ bool(vat_code):  # XOR used to check for "both or neither".
            raise ValidationError(_(u"Fill both the company name and VAT code fields."))
        else:
            if not (company_name or vat_code):
                return {}
        return self.cleaned_data


class AddressesPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "addresses"
    title = _(u"Addresses")

    template_name = "shoop/front/checkout/addresses.jinja"

    address_kinds = ("shipping", "billing")  # When adding to this, you'll naturally have to edit the template too
    address_form_class = AddressForm
    address_form_classes = {}  # Override by `address_kind` if required
    company_form_class = CompanyForm

    def get_form(self, form_class):
        fg = FormGroup(**self.get_form_kwargs())
        for kind in self.address_kinds:
            fg.add_form_def(kind, form_class=self.address_form_classes.get(kind, self.address_form_class))
        if self.company_form_class:
            fg.add_form_def("company", self.company_form_class, required=False)
        return fg

    def get_initial(self):
        initial = super(AddressesPhase, self).get_initial()
        for address_kind in self.address_kinds:
            if self.storage.get(address_kind):
                for key, value in model_to_dict(self.storage[address_kind]).items():
                    initial["%s-%s" % (address_kind, key)] = value
        return initial

    def is_valid(self):
        return self.storage.has_all(self.address_kinds)

    def form_valid(self, form):
        for key in self.address_kinds:
            self.storage[key] = form.forms[key].save(commit=False)
        if form.cleaned_data.get("company"):
            self.storage["company"] = form.forms["company"].save(commit=False)
        else:
            self.storage["company"] = None
        return super(AddressesPhase, self).form_valid(form)

    def _process_addresses(self, basket):
        for kind in self.address_kinds:
            setattr(basket, "%s_address" % kind, self.storage.get(kind))

    def process(self):
        basket = self.request.basket
        self._process_addresses(basket)
        if self.storage.get("company"):
            basket.customer = self.storage.get("company")
            for address in (basket.shipping_address, basket.billing_address):
                address.company_name = basket.customer.name
                address.vat_code = basket.customer.vat_code
