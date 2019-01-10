# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.models import model_to_dict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from shuup.core.models import (
    CompanyContact, SavedAddress, SavedAddressRole, SavedAddressStatus
)
from shuup.front.checkout import CheckoutPhaseViewMixin
from shuup.front.utils.companies import (
    allow_company_registration, TaxNumberCleanMixin
)
from shuup.utils.form_group import FormGroup
from shuup.utils.importing import cached_load


class CompanyForm(TaxNumberCleanMixin, forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = ("name", "tax_number",)

    def __init__(self, **kwargs):
        self.request = kwargs.pop("request")
        super(CompanyForm, self).__init__(**kwargs)
        self.fields["name"].required = False
        self.fields["tax_number"].required = False

    def clean(self):
        data = super(CompanyForm, self).clean()

        if data.get("name") and not data.get("tax_number"):
            self.add_error("tax_number", _("Tax number is required with the company name."))

        if data.get("tax_number") and not data.get("name"):
            self.add_error("name", _("Company name is required with the tax number."))

        return data


class SavedAddressForm(forms.Form):
    kind_to_role_map = {
        "shipping": SavedAddressRole.SHIPPING,
        "billing": SavedAddressRole.BILLING
    }

    addresses = forms.ChoiceField(label=_("Use a saved address"), required=False, choices=(), initial=None)

    def __init__(self, owner, kind, **kwargs):
        super(SavedAddressForm, self).__init__(**kwargs)
        saved_addr_qs = SavedAddress.objects.filter(owner=owner,
                                                    role=self.kind_to_role_map[kind],
                                                    status=SavedAddressStatus.ENABLED)
        saved_addr_choices = BLANK_CHOICE_DASH + [(addr.pk, addr.title) for addr in saved_addr_qs]
        self.fields["addresses"].choices = saved_addr_choices


class AddressesPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "addresses"
    title = _(u"Addresses")

    template_name = "shuup/front/checkout/addresses.jinja"

    # When adding to this, you'll naturally have to edit the template too
    address_kinds = ("shipping", "billing")
    address_form_classes = {}  # Override by `address_kind` if required
    company_form_class = CompanyForm
    saved_address_form_class = SavedAddressForm

    def get_form(self, form_class=None):
        fg = FormGroup(**self.get_form_kwargs())
        default_address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")
        for kind in self.address_kinds:
            fg.add_form_def(kind, form_class=self.address_form_classes.get(kind, default_address_form_class))
            fg.add_form_def("saved_{}".format(kind),
                            form_class=SavedAddressForm,
                            required=False,
                            kwargs={"kind": kind, "owner": self.basket.customer})

        if self.company_form_class and allow_company_registration(self.request.shop) and not self.request.customer:
            fg.add_form_def("company", self.company_form_class, required=False, kwargs={"request": self.request})

        return fg

    def get_initial(self):
        initial = super(AddressesPhase, self).get_initial()
        customer = self.basket.customer
        for address_kind in self.address_kinds:
            if self.storage.get(address_kind):
                address = self.storage.get(address_kind)
            elif customer:
                address = self._get_address_of_contact(customer, address_kind)
            else:
                address = None
            if address:
                for (key, value) in model_to_dict(address).items():
                    initial["%s-%s" % (address_kind, key)] = value
        return initial

    def _get_address_of_contact(self, contact, kind):
        if kind == 'billing':
            return contact.default_billing_address
        elif kind == 'shipping':
            return contact.default_shipping_address
        else:
            raise TypeError('Unknown address kind: %r' % (kind,))

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
        basket = self.basket
        self._process_addresses(basket)
        if self.storage.get("company"):
            basket.customer = self.storage.get("company")
            for address in (basket.shipping_address, basket.billing_address):
                address.company_name = basket.customer.name
                address.tax_number = basket.customer.tax_number

    def get_context_data(self, **kwargs):
        context = super(AddressesPhase, self).get_context_data(**kwargs)

        # generate all the available saved addresses if user wants to use some
        saved_addr_qs = SavedAddress.objects.filter(owner=self.basket.customer,
                                                    status=SavedAddressStatus.ENABLED)
        context["saved_address"] = {}
        for saved_address in saved_addr_qs:
            data = {}

            for key, value in model_to_dict(saved_address.address).items():
                if value:
                    data[key] = force_text(value)

            context["saved_address"][saved_address.pk] = data

        return context
