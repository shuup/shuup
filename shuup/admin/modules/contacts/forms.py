# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries import countries
from django_countries.fields import LazyTypedChoiceField
from enumfields import EnumField

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.forms.widgets import (
    FileDnDUploaderWidget,
    PersonContactChoiceWidget,
    QuickAddContactGroupMultiSelect,
    QuickAddTaxGroupSelect,
)
from shuup.admin.shop_provider import get_shop
from shuup.core.fields import LanguageFormField
from shuup.core.models import CompanyContact, Contact, ContactGroup, Gender, PersonContact, Shop
from shuup.utils.django_compat import force_text

FIELDS_BY_MODEL_NAME = {
    "Contact": (
        "is_active",
        "marketing_permission",
        "phone",
        "www",
        "timezone",
        "prefix",
        "suffix",
        "name_ext",
        "email",
        "tax_group",
        "merchant_notes",
        "account_manager",
        "picture",
    ),
    "PersonContact": ("first_name", "last_name", "gender", "language", "birth_date"),
    "CompanyContact": ("name", "tax_number", "members"),
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
            widget=QuickAddContactGroupMultiSelect(attrs={"data-model": "shuup.ContactGroup"}),
            label=_("Contact Groups"),
            help_text=_(
                "The contact groups this contact belongs to. Contact groups are defined in Contacts - Contact Groups "
                "and are used to configure sales, campaigns, and product pricing tailored for a set of users."
            ),
        )
        if "account_manager" in self.fields:
            self.fields["account_manager"].widget = PersonContactChoiceWidget(clearable=True)

        if "picture" in self.fields:
            self.fields["picture"].widget = FileDnDUploaderWidget(
                upload_path="/contacts", kind="images", clearable=True
            )

        if not self.request or (self.request and self.request.user.is_superuser):
            shops_qs = Shop.objects.all()
        else:
            shops_qs = Shop.objects.filter(staff_members__in=[self.request.user])

        if "tax_group" in self.fields:
            self.fields["tax_group"].widget = QuickAddTaxGroupSelect(editable_model="shuup.CustomerTaxGroup")
            if self.instance and self.instance.tax_group:
                self.fields["tax_group"].widget.choices = [(self.instance.tax_group.id, self.instance.tax_group.name)]

        self.fields["shops"] = forms.ModelMultipleChoiceField(
            queryset=shops_qs,
            initial=(self.instance.shops.all() if self.instance.pk else ()),
            required=False,
            widget=forms.SelectMultiple(),
            label=_("Shops"),
            help_text=_("The shops this contact belongs to"),
        )

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.is_active = True
        obj = super(ContactBaseFormMixin, self).save(commit)
        shop = get_shop(self.request)
        obj.groups.set([obj.get_default_group()] + list(self.cleaned_data["groups"]))
        obj.add_to_shops(shop, list(self.cleaned_data["shops"]))
        return obj


class PersonContactBaseForm(ContactBaseFormMixin, forms.ModelForm):
    language = LanguageFormField(
        label=_("Language"),
        required=False,
        include_blank=True,
        help_text=_("The primary language to be used in all communications with the contact."),
    )

    class Meta:
        model = PersonContact
        fields = list(FIELDS_BY_MODEL_NAME["PersonContact"]) + list(FIELDS_BY_MODEL_NAME["Contact"])

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        self.request = kwargs.pop("request", None)
        super(PersonContactBaseForm, self).__init__(*args, **kwargs)

    def init_fields(self):
        super(PersonContactBaseForm, self).init_fields()
        for field_name in ("first_name", "last_name"):
            self.fields[field_name].required = True
        self.initial["language"] = self.instance.language

    def save(self, commit=True):
        self.instance.name = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]
        self.instance.language = self.cleaned_data["language"]
        obj = super(PersonContactBaseForm, self).save(commit)
        if self.user and not getattr(obj, "user", None):  # Allow binding only once
            obj.user = self.user
            obj.save()
        return obj


class CompanyContactBaseForm(ContactBaseFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = list(FIELDS_BY_MODEL_NAME["CompanyContact"]) + list(FIELDS_BY_MODEL_NAME["Contact"])

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(CompanyContactBaseForm, self).__init__(*args, **kwargs)

    def init_fields(self):
        super(CompanyContactBaseForm, self).init_fields()
        self.fields["name"].help_text = _("The company name.")
        members_field = Select2MultipleField(
            model=PersonContact, required=False, help_text=_("The contacts that are members of this company.")
        )
        if self.instance.pk and hasattr(self.instance, "members"):
            members_field.widget.choices = [(object.pk, force_text(object)) for object in self.instance.members.all()]
        self.fields["members"] = members_field


class MassEditForm(forms.Form):
    gender = EnumField(Gender).formfield(default=Gender.UNDISCLOSED, label=_("Gender"), required=False)
    merchant_notes = forms.CharField(label=_("Merchant Notes"), widget=forms.Textarea, required=False)
    www = forms.URLField(required=False, label=_("Website URL"))
    account_manager = forms.ModelChoiceField(PersonContact.objects.all(), label=_("Account Manager"), required=False)
    tax_number = forms.CharField(label=_("Company: Tax Number"), max_length=32, required=False)
    members = forms.ModelMultipleChoiceField(Contact.objects.all(), label=_("Company: Members"), required=False)
    language = LazyTypedChoiceField(
        choices=[("", _("Select Language"))] + list(countries), label=_("Language"), required=False
    )


class GroupMassEditForm(forms.Form):
    contact_group = forms.ModelMultipleChoiceField(ContactGroup.objects.all(), label=_("Contact Group"), required=False)
