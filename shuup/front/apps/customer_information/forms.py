# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from shuup.core.models import CompanyContact, MutableAddress, PersonContact


class PersonContactForm(forms.ModelForm):
    class Meta:
        model = PersonContact
        fields = ("first_name", "last_name", "phone", "email", "gender", "marketing_permission")

    def __init__(self, *args, **kwargs):
        super(PersonContactForm, self).__init__(*args, **kwargs)
        for field in ("first_name", "last_name", "email"):
            self.fields[field].required = True


class AddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = ("name", "phone", "email", "street", "street2", "postal_code", "city", "region", "country")

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        for field in ("email", "postal_code"):
            self.fields[field].required = True


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
