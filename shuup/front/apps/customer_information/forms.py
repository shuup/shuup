# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField
from registration.signals import user_registered

from shuup.core.fields import LanguageFormField
from shuup.core.models import (
    CompanyContact, get_company_contact, get_person_contact, MutableAddress,
    PersonContact, SavedAddress, SavedAddressRole, SavedAddressStatus
)
from shuup.front.forms.widget import PictureDnDUploaderWidget
from shuup.front.utils.companies import company_registration_requires_approval
from shuup.utils.form_group import FormGroup
from shuup.utils.importing import cached_load

from .notify_events import CompanyAccountCreated


class PersonContactForm(forms.ModelForm):
    language = LanguageFormField(label=_("Language"), required=False)

    class Meta:
        model = PersonContact
        fields = (
            "first_name", "last_name", "phone", "email", "gender", "language",
            "marketing_permission", "timezone", "picture"
        )

    def __init__(self, *args, **kwargs):
        super(PersonContactForm, self).__init__(*args, **kwargs)
        for field in ("first_name", "last_name", "email"):
            self.fields[field].required = True
        self.initial["language"] = self.instance.language

        if settings.SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD:
            self.fields["picture"].widget = PictureDnDUploaderWidget(clearable=True)
        else:
            self.fields.pop("picture")

        field_properties = settings.SHUUP_PERSON_CONTACT_FIELD_PROPERTIES
        for field, properties in field_properties.items():
            for prop in properties:
                setattr(self.fields[field], prop, properties[prop])

    def save(self, commit=True):
        self.instance.language = self.cleaned_data["language"]
        return super(PersonContactForm, self).save(commit)


class CompanyContactForm(forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = (
            "name", "tax_number", "phone", "email", "marketing_permission", "picture"
        )

    def __init__(self, *args, **kwargs):
        super(CompanyContactForm, self).__init__(*args, **kwargs)

        if settings.SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD:
            self.fields["picture"].widget = PictureDnDUploaderWidget(clearable=True)
        else:
            self.fields.pop("picture")

        for field in ("name", "tax_number", "email"):
            self.fields[field].required = True
        if not kwargs.get("instance"):
            self.fields["email"].help_text = _("Will become default user email when linked.")

    def clean_tax_number(self):
        """
        Clean Tax Number.

        This is done because we want to prevent duplicates in the front-end.
        """
        tax_number = self.cleaned_data["tax_number"]
        company = CompanyContact.objects.filter(tax_number=tax_number).first()
        if company:
            error_message = _("Given Tax Number already exists. Please contact support.")
            if not self.instance.pk:
                raise ValidationError(error_message, code="existing_tax_number")
            elif company.pk != self.instance.pk:
                raise ValidationError(error_message, code="existing_tax_number")
        return tax_number


class SavedAddressForm(forms.Form):
    title = forms.CharField(max_length=255, label=_("Address Title"))
    role = EnumField(SavedAddressRole, default=SavedAddressRole.SHIPPING).formfield(label=_("Address Type"))
    status = EnumField(SavedAddressStatus, default=SavedAddressStatus.ENABLED).formfield(label=_("Address Status"))


class CustomerInformationFormGroup(FormGroup):
    address_forms = ["billing", "shipping"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(CustomerInformationFormGroup, self).__init__(*args, **kwargs)
        contact = get_person_contact(self.request.user)
        address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")

        for form_name in self.address_forms:
            self.add_form_def(form_name, address_form_class, kwargs={
                "instance": getattr(contact, "default_%s_address" % form_name)
            })

        self.add_form_def("contact", PersonContactForm, kwargs={"instance": contact})

    def save(self):
        contact = self.forms["contact"].save()
        user = contact.user

        if "billing" in self.forms:
            billing_address = self.forms["billing"].save()
            if billing_address.pk != contact.default_billing_address_id:  # Identity changed due to immutability
                contact.default_billing_address = billing_address

        if "shipping" in self.forms:
            shipping_address = self.forms["shipping"].save()
            if shipping_address.pk != contact.default_shipping_address_id:  # Identity changed due to immutability
                contact.default_shipping_address = shipping_address

        if not bool(get_company_contact(self.request.user)):  # Only update user details for non-company members
            user.email = contact.email
            user.first_name = contact.first_name
            user.last_name = contact.last_name
            user.save()

        contact.save()
        return contact


class CompanyInformationFormGroup(FormGroup):
    address_forms = ["billing", "shipping"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(CompanyInformationFormGroup, self).__init__(*args, **kwargs)

        user = self.request.user
        company = get_company_contact(user)
        person = get_person_contact(user)
        address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")

        for form_name in self.address_forms:
            self.add_form_def(
                form_name,
                address_form_class,
                kwargs={
                    "instance": _get_default_address_for_contact(company, "default_%s_address" % form_name, person)
                }
            )
        self.add_form_def("contact", CompanyContactForm, kwargs={"instance": company})

    def save(self):
        company = self.forms["contact"].save(commit=False)
        is_new = not bool(company.pk)
        company.save()
        user = self.request.user

        # TODO: Should this check if contact will be created? Or should we expect create always?
        person = get_person_contact(user)
        person.add_to_shop(self.request.shop)
        company.members.add(person)
        company.add_to_shop(self.request.shop)

        if "billing" in self.forms:
            billing_address = self.forms["billing"].save()
            if billing_address.pk != company.default_billing_address_id:  # Identity changed due to immutability
                company.default_billing_address = billing_address

        if "shipping" in self.forms:
            shipping_address = self.forms["shipping"].save()
            if shipping_address.pk != company.default_shipping_address_id:  # Identity changed due to immutability
                company.default_shipping_address = shipping_address

        message = _("Company information was saved.")
        # If company registration requires activation,
        # company will be created as inactive.
        if is_new and company_registration_requires_approval(self.request.shop):
            company.is_active = False
            message = _("Company information was saved. "
                        "Please follow the instructions sent to your email address.")

        messages.success(self.request, message)
        company.save()

        if is_new:
            user_registered.send(sender=self.__class__, user=self.request.user, request=self.request)
            CompanyAccountCreated(contact=company, customer_email=company.email).run(shop=self.request.shop)

        return company


class AddressBookFormGroup(FormGroup):
    saved_address_form = SavedAddressForm

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.instance = kwargs.pop("instance")
        super(AddressBookFormGroup, self).__init__(*args, **kwargs)
        address_kwargs = {}
        saved_address_kwargs = {}

        if self.instance:
            address_kwargs["instance"] = self.instance.address
            saved_address_kwargs["initial"] = {
                "role": self.instance.role,
                "status": self.instance.status,
                "title": self.instance.title,
            }

        self.add_form_def("address", cached_load("SHUUP_ADDRESS_MODEL_FORM"), kwargs=address_kwargs)
        self.add_form_def("saved_address", self.saved_address_form, kwargs=saved_address_kwargs)

    def save(self):
        address_form = self.forms["address"]
        if self.instance:
            # expect old
            address = MutableAddress.objects.get(pk=self.instance.address.pk)
            for k, v in six.iteritems(address_form.cleaned_data):
                setattr(address, k, v)
            address.save()
        else:
            address = address_form.save()
        owner = self.request.customer
        saf = self.forms["saved_address"]
        saved_address, updated = SavedAddress.objects.update_or_create(
            owner=owner,
            address=address,
            defaults={
                "title": saf.cleaned_data.get("title"),
                "role": saf.cleaned_data.get("role"),
                "status": saf.cleaned_data.get("status")
            }
        )
        return saved_address


def _get_default_address_for_contact(contact, address_attr, fallback_contact):
    if contact and getattr(contact, address_attr, None):
        return getattr(contact, address_attr)
    if fallback_contact and getattr(fallback_contact, address_attr, None):
        return getattr(fallback_contact, address_attr)
    return None
