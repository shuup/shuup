# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from shuup.core.fields import LanguageFormField
from shuup.core.models import (
    CompanyContact, PersonContact, SavedAddressRole, SavedAddressStatus
)


class PersonContactForm(forms.ModelForm):
    language = LanguageFormField(label=_("Language"), required=False)

    class Meta:
        model = PersonContact
        fields = ("first_name", "last_name", "phone", "email", "gender", "language", "marketing_permission")

    def __init__(self, *args, **kwargs):
        super(PersonContactForm, self).__init__(*args, **kwargs)
        for field in ("first_name", "last_name", "email"):
            self.fields[field].required = True
        self.initial["language"] = self.instance.language

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
        fields = ("name", "tax_number", "phone", "email", "marketing_permission")

    def __init__(self, *args, **kwargs):
        super(CompanyContactForm, self).__init__(*args, **kwargs)
        for field in ("name", "tax_number", "email"):
            self.fields[field].required = True
        if not kwargs.get("instance"):
            self.fields["email"].help_text = _("Will become default user email when linked")

    def clean_tax_number(self):
        """
        Clean Tax Number

        This is done because we want to prevent duplicates in front-end
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
