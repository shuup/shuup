# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
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
            label=_("Currency")
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
