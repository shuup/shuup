# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms import ShuupAdminForm
from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.forms.widgets import (
    QuickAddLabelMultiSelect, QuickAddUserMultiSelect
)
from shuup.core.models import Currency, MutableAddress, Shop
from shuup.core.settings_provider import ShuupSettings
from shuup.core.utils.form_mixins import ProtectedFieldsMixin
from shuup.utils.django_compat import force_text
from shuup.utils.i18n import get_current_babel_locale


def get_currency_choices():
    locale = get_current_babel_locale()
    currencies = Currency.objects.all().order_by("code")
    return [(currency.code, locale.currencies.get(currency.code, currency)) for currency in currencies]


class ShopBaseForm(ProtectedFieldsMixin, ShuupAdminForm):
    change_protect_field_text = _("This field cannot be changed since there are existing orders for this shop.")

    class Meta:
        model = Shop
        exclude = ("owner", "options", "contact_address")
        widgets = {
            "labels": QuickAddLabelMultiSelect(),
        }

    def __init__(self, **kwargs):
        super(ShopBaseForm, self).__init__(**kwargs)
        self.fields["currency"] = forms.ChoiceField(
            choices=get_currency_choices(),
            required=True,
            label=_("Currency"),
            help_text=_("The primary shop currency. This is the currency used when selling your products.")
        )

        staff_members = Select2MultipleField(
            label=_("Staff"),
            help_text=_("Select staff members for this shop."),
            model=get_user_model(),
            required=False
        )
        staff_members.widget = QuickAddUserMultiSelect(attrs={"data-model": "auth.User"})
        initial_members = (self.instance.staff_members.all() if self.instance.pk else [])
        staff_members.widget.choices = [(member.pk, force_text(member)) for member in initial_members]
        self.fields["staff_members"] = staff_members
        self.fields["domain"].required = ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS")
        self.disable_protected_fields()

    def clean_domain(self):
        domain = self.cleaned_data["domain"]
        if not domain:
            return None
        if Shop.objects.filter(domain=domain).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("Domain is unique. Please enter a unique value."), code="invalid_domain")
        return domain


class ContactAddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "prefix", "name", "suffix", "name_ext",
            "phone", "email",
            "street", "street2", "street3",
            "postal_code", "city",
            "region_code", "region",
            "country", "tax_number",
            "latitude", "longitude"
        )


class ShopWizardForm(ShuupAdminForm):
    class Meta:
        model = Shop
        fields = ("public_name", "logo", "currency", "prices_include_tax")
        labels = {
            "public_name": _("Shop name")
        }

    def __init__(self, **kwargs):
        super(ShopWizardForm, self).__init__(**kwargs)
        self.fields["currency"] = forms.ChoiceField(
            choices=get_currency_choices(),
            required=True,
            label=_("Currency"),
            help_text=_("The primary shop currency. This is the currency used when selling your products.")
        )

    def save(self):
        obj = super(ShopWizardForm, self).save()
        for language in settings.LANGUAGES:
            public_name = self.cleaned_data.get("public_name__%s" % language[0])
            if public_name:
                obj.set_current_language(language[0])
                obj.name = obj.public_name
            obj.save()


class ShopAddressWizardForm(forms.ModelForm):
    first_name = forms.CharField(label=_("First name"), help_text=_("Your first name."))
    last_name = forms.CharField(label=_("Last name"), help_text=_("Your last name."))

    class Meta:
        model = MutableAddress
        fields = (
            "first_name", "last_name", "phone", "street", "street2", "postal_code", "city", "country",
            "region_code", "region"
        )
        widgets = {
            "region_code": forms.Select(choices=[])
        }
        labels = {
            "postal_code": _("Zip/Postal code"),
            "region_code": _("State/Province"),
            "street": _("Address"),
            "street2": _("Address (2)")
        }
        help_texts = {
            "street": _("The shop street address. This may be used to provide estimated shipping costs."),
            "postal_code": _("The shop zip/postal code."),
            "city": _("The city in which your shop is located."),
            "country": _("The country in which your shop is located.")
        }

    def __init__(self, **kwargs):
        self.user = kwargs.pop("user")
        super(ShopAddressWizardForm, self).__init__(**kwargs)
        self.fields["postal_code"].required = True
        self.fields["phone"].required = True

        if not self.instance.pk:
            self.fields["country"].initial = settings.SHUUP_ADDRESS_HOME_COUNTRY

        if self.instance.pk:
            name_components = self.instance.name.split(" ")
            first_name = ""
            last_name = ""
            if len(name_components) >= 2:
                first_name = name_components[0]
                last_name = " ".join(name_components[1:])
            self.fields["first_name"].initial = first_name
            self.fields["last_name"].initial = last_name

    def save(self):
        obj = super(ShopAddressWizardForm, self).save()
        obj.name = "%s %s" % (self.cleaned_data.get("first_name"), self.cleaned_data.get("last_name"))
        obj.save()
        return obj
