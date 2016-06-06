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
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from shoop.core.models import CompanyContact, MutableAddress
from shoop.front.checkout import CheckoutPhaseViewMixin
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

        field_properties = settings.SHOOP_FRONT_ADDRESS_FIELD_PROPERTIES
        for field, properties in field_properties.items():
            for prop in properties:
                setattr(self.fields[field], prop, properties[prop])


class CompanyForm(TaxNumberCleanMixin, forms.ModelForm):
    company_name_field = "name"

    class Meta:
        model = CompanyContact
        fields = ("name", "tax_number",)


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
        if self.company_form_class and not self.request.customer:
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
                address.tax_number = basket.customer.tax_number
