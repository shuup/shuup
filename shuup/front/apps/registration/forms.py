# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django import forms
from django.contrib.auth.forms import User, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from registration.users import UsernameField

from shuup.core.models import CompanyContact, MutableAddress, PersonContact


class CompanyRegistrationForm(UserCreationForm):
    """
    Form for registering a new account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    required_css_class = 'required'
    email = forms.EmailField(label=_("E-mail"))

    contact_first_name = forms.CharField(max_length=255, label=_("First Name"))
    contact_last_name = forms.CharField(max_length=255, label=_("Last Name"))
    contact_phone = forms.CharField(
        label=_('Phone'), max_length=64, help_text=_("The primary phone number for the address."))
    contact_street = forms.CharField(
        label=_('Street'), max_length=255, help_text=_("The street address."))
    contact_street2 = forms.CharField(
        label=_('Street (2)'), required=False, max_length=255,
        help_text=_("An additional street address line."))
    contact_street3 = forms.CharField(
        label=_('Street (3)'), required=False, max_length=255,
        help_text=_("Any additional street address line."))
    contact_postal_code = forms.CharField(
        label=_('Postal Code'), max_length=64, help_text=_("The address postal/zip code."))
    contact_city = forms.CharField(label=_('City'), max_length=255, help_text=_("The address city."))
    contact_region_code = forms.CharField(
        label=_('Region Code'), required=False, max_length=16,
        help_text=_("The address region, province, or state."))
    contact_region = forms.CharField(
        label=_('Region'), required=False, max_length=64,
        help_text=_("The address region, province, or state."))
    contact_country = forms.ChoiceField(choices=countries, label=_("Country"), widget=CountrySelectWidget)
    company_name = forms.CharField(
        label=_('Name'), max_length=255, help_text=_("The name for the address."))
    company_name_ext = forms.CharField(
        label=_('Name Extension'), required=False, max_length=255,
        help_text=_(
            "Any other text to display along with the address. "
            "This could be department names (for companies) or titles (for people)."))
    company_www = forms.URLField(max_length=128, required=False, label=_("Web Address"))
    company_tax_number = forms.CharField(
        label=_('Tax Number'), max_length=32,
        help_text=_("The business tax number. For example, EIN in US or VAT code in Europe."))
    company_email = forms.EmailField(
        label=_('Email'), max_length=128, help_text=_("The primary email for the address."))
    company_phone = forms.CharField(
        label=_('Phone'), max_length=64, help_text=_("The primary phone number for the address."))
    company_street = forms.CharField(
        label=_('Street'), max_length=255, help_text=_("The street address."))
    company_street2 = forms.CharField(
        label=_('Street (2)'), max_length=255, help_text=_("An additional street address line."), required=False)
    company_street3 = forms.CharField(
        label=_('Street (3)'), required=False, max_length=255,
        help_text=_("Any additional street address line."))
    company_postal_code = forms.CharField(
        label=_('Postal Code'), max_length=64, help_text=_("The address postal/zip code."))
    company_city = forms.CharField(label=_('City'), max_length=255, help_text=_("The address city."))
    company_region_code = forms.CharField(
        label=_('Region Code'), required=False, max_length=16,
        help_text=_("The address region, province, or state."))
    company_region = forms.CharField(
        label=_('Region'), required=False, max_length=64,
        help_text=_("The address region, province, or state."))
    company_country = forms.ChoiceField(choices=countries, label=_("Country"), widget=CountrySelectWidget)

    class Meta:
        model = User
        fields = (UsernameField(), "email")

    def save(self, commit=True):

        def populate_address(needle):
            data = {}
            delete = []
            for k, value in six.iteritems(self.cleaned_data):
                if k.startswith(needle):
                    key = k.replace(needle, "")
                    data[key] = value
                    delete.append(k)

            # sweep unneeded keys
            for k in delete:
                del self.cleaned_data[k]

            return data

        contact_address_data = populate_address("contact_")
        company_address_data = populate_address("company_")
        user = super(CompanyRegistrationForm, self).save(commit)

        website = company_address_data.pop("www")

        contact_address = MutableAddress.from_data(contact_address_data)
        contact_address.save()
        company_address = MutableAddress.from_data(company_address_data)
        company_address.save()

        contact = PersonContact()
        contact.is_active = False
        contact.user = user
        contact.email = user.email
        contact.default_shipping_address = contact_address
        contact.default_billing_address = contact_address
        contact.first_name = contact_address_data["first_name"]
        contact.last_name = contact_address_data["last_name"]
        contact.phone = contact_address.phone
        contact.save()

        company = CompanyContact()
        company.default_shipping_address = company_address
        company.default_billing_address = company_address
        company.is_active = False
        company.phone = company_address.phone
        company.www = website
        company.name = company_address_data["name"]
        company.name_ext = company_address_data["name_ext"]
        company.tax_number = company_address_data["tax_number"]
        company.email = company_address_data["email"]
        company.save()
        company.members.add(contact)
        return user
