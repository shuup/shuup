# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Shop
from shuup.core.settings_provider import ShuupSettings
from shuup.utils.i18n import get_currency_name


class StockAdjustmentForm(forms.Form):
    purchase_price = forms.DecimalField(
        label=_("Purchase price per unit (%(currency_name)s)") % {
            "currency_name": get_currency_name(settings.SHUUP_HOME_CURRENCY)
        }
    )
    delta = forms.DecimalField(label=_("Quantity"))

    def __init__(self, *args, **kwargs):
        super(StockAdjustmentForm, self).__init__(*args, **kwargs)
        if not ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            self.fields["purchase_price"].label = "Purchase price per unit (%(currency_name)s)" % {
                "currency_name": get_currency_name(Shop.objects.first().currency)
            }

    def clean_delta(self):
        delta = self.cleaned_data.get("delta")
        if delta == 0:
            raise ValidationError(_("Only non-zero values can be added to stock."), code="stock_delta_zero")

        return delta


class AlertLimitForm(forms.Form):
    alert_limit = forms.DecimalField(label=_("Alert limit"))


class StockManagedForm(forms.Form):
    stock_managed = forms.BooleanField(widget=forms.HiddenInput())
