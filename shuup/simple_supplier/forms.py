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

from shuup.admin.forms.fields import DecimalPlaceField
from shuup.core.models import Shop
from shuup.core.settings_provider import ShuupSettings
from shuup.utils.i18n import get_currency_name


class StockAdjustmentForm(forms.Form):
    purchase_price = forms.DecimalField(
        label=format_lazy(
            _("Purchase price per unit ({currency_name})"),
            currency_name=get_currency_name(settings.SHUUP_HOME_CURRENCY),
        )
    )
    delta = DecimalPlaceField(label=_("Quantity"))
    decimal_places = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.decimals = 0
        if len(args) > 0 and "decimal_places" in args[0]:
            self.decimals = int(args[0]["decimal_places"])
        super(StockAdjustmentForm, self).__init__(*args, **kwargs)
        if not ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            self.fields["purchase_price"].label = format_lazy(
                _("Purchase price per unit ({currency_name})"),
                currency_name=get_currency_name(Shop.objects.first().currency),
            )
        if self.decimals == 0 and "decimal_places" in self.initial:
            self.decimals = self.initial["decimal_places"]
        else:
            if self.decimals == 0 and "decimal_places" in self.data:
                self.decimals = self.data["decimal_places"]
        self.fields["delta"].decimal_places = self.decimals
        self.fields["delta"].widget = DecimalPlaceField(label=_("Quantity"), decimal_places=self.decimals).widget

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
    alert_limit = forms.DecimalField(label=_("Alert limit"))


class StockManagedForm(forms.Form):
    stock_managed = forms.BooleanField(widget=forms.HiddenInput())
