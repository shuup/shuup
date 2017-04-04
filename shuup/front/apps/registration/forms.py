# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib.auth.forms import User, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from registration.users import UsernameField

from shuup.core.models import CompanyContact, MutableAddress, PersonContact


def _form_field_from(model, field_name, **kwargs):
    return model._meta.get_field(field_name).formfield(**kwargs)


def _address_field(field_name, **kwargs):
    return _form_field_from(MutableAddress, field_name, **kwargs)


def _person_field(field_name, **kwargs):
    kwargs.setdefault('help_text', None)
    return _form_field_from(PersonContact, field_name, **kwargs)


def _company_field(field_name, **kwargs):
    return _form_field_from(CompanyContact, field_name, **kwargs)


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
    email = _form_field_from(User, 'email')

    contact_first_name = _person_field('first_name', required=True)
    contact_last_name = _person_field('last_name', required=True)
    contact_phone = _address_field('phone', required=True, help_text=None)
    contact_street = _address_field('street')
    contact_street2 = _address_field('street2')
    contact_street3 = _address_field('street3')
    contact_postal_code = _address_field('postal_code')
    contact_city = _address_field('city')
    contact_region_code = _address_field('region_code')
    contact_region = _address_field('region')
    contact_country = _address_field('country')

    company_name = _company_field('name', help_text=_("Name of the company"))
    company_name_ext = _company_field('name_ext')
    company_www = _company_field('www', help_text=None)
    company_tax_number = _company_field('tax_number')
    company_email = _company_field('email')
    company_phone = _company_field('phone', help_text=None)
    company_street = _address_field('street')
    company_street2 = _address_field('street2')
    company_street3 = _address_field('street3')
    company_postal_code = _address_field('postal_code')
    company_city = _address_field('city')
    company_region_code = _address_field('region_code')
    company_region = _address_field('region')
    company_country = _address_field('country')

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
