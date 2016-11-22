# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.widgets import MediaChoiceWidget
from shuup.core.models import Currency, MutableAddress, Shop
from shuup.core.utils.form_mixins import ProtectedFieldsMixin
from shuup.utils.i18n import get_current_babel_locale
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


def get_currency_choices():
    locale = get_current_babel_locale()
    currencies = Currency.objects.all().order_by("code")
    return [(currency.code, locale.currencies.get(currency.code, currency)) for currency in currencies]


class ShopBaseForm(ProtectedFieldsMixin, MultiLanguageModelForm):
    change_protect_field_text = _("This field cannot be changed since there are existing orders for this shop.")

    class Meta:
        model = Shop
        exclude = ("owner", "options", "contact_address")

    def __init__(self, **kwargs):
        super(ShopBaseForm, self).__init__(**kwargs)
        self.fields["logo"].widget = MediaChoiceWidget(clearable=True)
        self.fields["currency"] = forms.ChoiceField(
            choices=get_currency_choices(),
            required=True,
            label=_("Currency"),
            help_text=_("The primary shop currency. This is the currency used when selling your products.")
        )
        self.disable_protected_fields()


class ContactAddressForm(forms.ModelForm):
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


class ShopWizardForm(MultiLanguageModelForm):
    class Meta:
        model = Shop
        fields = ("public_name", "currency", "prices_include_tax")
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
    class Meta:
        model = MutableAddress
        fields = ("name", "street", "postal_code", "city", "country", "region_code", "region")
        widgets = {
            "region_code": forms.Select(choices=[])
        }
        labels = {
            "name": _("Shop Owner Name"),
            "postal_code": _("Zip/Postal code"),
            "region_code": _("State/Province")
        }
        help_texts = {
            "name": _("The name of primary shop contact person."),
            "street": _("The shop street address. This may be used to provide estimated shipping costs."),
            "postal_code": _("The shop zip/postal code."),
            "city": _("The city in which your shop is located."),
            "country": _("The country in which your shop is located.")
        }
