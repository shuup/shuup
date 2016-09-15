# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shuup.core.settings import SHUUP_HOME_CURRENCY
from shuup.utils.i18n import get_currency_name


class StockAdjustmentForm(forms.Form):
    purchase_price = forms.DecimalField(
        label=_("Purchase price per unit (%(currency_name)s)") % {
            "currency_name": get_currency_name(SHUUP_HOME_CURRENCY)
        }
    )
    delta = forms.DecimalField(label=_("Quantity"))

    def clean_delta(self):
        delta = self.cleaned_data.get("delta")
        if delta == 0:
            raise ValidationError(_("Only non-zero values can be added to stock."), code="stock_delta_zero")

        return delta


class AlertLimitForm(forms.Form):
    alert_limit = forms.DecimalField(label=_("Alert limit"))
