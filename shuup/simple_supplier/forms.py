# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _
from typing import Optional

from shuup.core.fields import FormattedDecimalFormField
from shuup.core.models import SalesUnit, Shop
from shuup.core.settings_provider import ShuupSettings
from shuup.utils.i18n import get_currency_name


class StockAdjustmentForm(forms.Form):
    purchase_price = forms.DecimalField(
        label=format_lazy(
            _("Purchase price per unit ({currency_name})"),
            currency_name=get_currency_name(settings.SHUUP_HOME_CURRENCY),
        )
    )
    delta = FormattedDecimalFormField(label=_("Quantity"), decimal_places=0)

    def __init__(self, sales_unit: Optional[SalesUnit] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            self.fields["purchase_price"].label = format_lazy(
                _("Purchase price per unit ({currency_name})"),
                currency_name=get_currency_name(Shop.objects.first().currency),
            )
        self.decimals = 0
        if sales_unit:
            self.decimals = sales_unit.decimals
            self.fields["delta"] = FormattedDecimalFormField(label=_("Quantity"), decimal_places=sales_unit.decimals)

    def clean_delta(self):
        delta = self.cleaned_data.get("delta")
        if delta == 0:
            raise ValidationError(_("Only non-zero values can be added to stock."), code="stock_delta_zero")

        if self.decimals:
            precision = Decimal("0.1") ** self.decimals
        else:
            precision = Decimal("1")
        return Decimal(delta).quantize(precision)


class AlertLimitForm(forms.Form):
    alert_limit = forms.DecimalField(label=_("Alert limit"), decimal_places=0)

    def __init__(self, sales_unit: Optional[SalesUnit] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.decimals = 0
        if sales_unit:
            self.decimals = sales_unit.decimals
            self.fields["alert_limit"] = forms.DecimalField(label=_("Alert limit"), decimal_places=sales_unit.decimals)

    def clean_alert_limit(self):
        alert_limit = self.cleaned_data.get("alert_limit")
        if self.decimals:
            precision = Decimal("0.1") ** self.decimals
        else:
            precision = Decimal("1")

        return Decimal(alert_limit).quantize(precision)


class StockManagedForm(forms.Form):
    stock_managed = forms.BooleanField(widget=forms.HiddenInput())
