# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.forms.widgets import PersonContactChoiceWidget
from shuup.core.models import (
    CompanyContact, ContactGroup, MutableAddress, PersonContact
)

FIELDS_BY_MODEL_NAME = {
    "Contact": (
        "is_active", "language", "marketing_permission", "phone", "www",
        "timezone", "prefix", "suffix", "name_ext", "email", "tax_group",
        "merchant_notes", "account_manager"
    ),
    "PersonContact": (
        "first_name", "last_name", "gender", "birth_date"
    ),
    "CompanyContact": (
        "name", "tax_number", "members"
    )
}


class ContactBaseFormMixin(object):
    def __init__(self, *args, **kwargs):
        super(ContactBaseFormMixin, self).__init__(*args, **kwargs)
        self.init_fields()

    def init_fields(self):
        self.fields["groups"] = forms.ModelMultipleChoiceField(
            queryset=ContactGroup.objects.all_except_defaults(),
            initial=(self.instance.groups.all_except_defaults() if self.instance.pk else ()),
            required=False,
            widget=forms.SelectMultiple(),
            label=_("Contact Groups")
        )
        if "account_manager" in self.fields:
            self.fields["account_manager"].widget = PersonContactChoiceWidget(clearable=True)

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.is_active = True
        obj = super(ContactBaseFormMixin, self).save(commit)
        obj.groups = [obj.get_default_group()] + list(self.cleaned_data["groups"])
        return obj


class PersonContactBaseForm(ContactBaseFormMixin, forms.ModelForm):
    class Meta:
        model = PersonContact
        fields = list(FIELDS_BY_MODEL_NAME["PersonContact"]) + list(FIELDS_BY_MODEL_NAME["Contact"])

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(PersonContactBaseForm, self).__init__(*args, **kwargs)

    def init_fields(self):
        super(PersonContactBaseForm, self).init_fields()
        for field_name in ("first_name", "last_name"):
            self.fields[field_name].required = True

    def save(self, commit=True):
        self.instance.name = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]
        obj = super(PersonContactBaseForm, self).save(commit)
        if self.user and not getattr(obj, "user", None):  # Allow binding only once
            obj.user = self.user
            obj.save()
        return obj


class CompanyContactBaseForm(ContactBaseFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = list(FIELDS_BY_MODEL_NAME["CompanyContact"]) + list(FIELDS_BY_MODEL_NAME["Contact"])

    def init_fields(self):
        super(CompanyContactBaseForm, self).init_fields()
        members_field = Select2MultipleField(model=PersonContact, required=False)
        if self.instance.pk and hasattr(self.instance, "members"):
            members_field.widget.choices = [
                (object.pk, force_text(object)) for object in self.instance.members.all()
            ]
        self.fields["members"] = members_field


class AddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "prefix", "name", "suffix", "name_ext",
            "phone", "email",
            "street", "street2", "street3",
            "postal_code", "city",
            "region_code", "region",
            "country"
        )
