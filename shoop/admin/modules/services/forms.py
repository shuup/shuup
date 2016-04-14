# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms import ShoopAdminForm
from shoop.core.models import (
    FixedCostBehaviorComponent, PaymentMethod, ShippingMethod,
    WaivingCostBehaviorComponent, WeightLimitsBehaviorComponent
)


class BaseMethodForm(ShoopAdminForm):
    class Meta:
        model = None
        exclude = [
            "identifier", "behavior_components", "old_module_identifier",
            "old_module_data"
        ]

    def __init__(self, **kwargs):
        super(BaseMethodForm, self).__init__(**kwargs)
        self.fields["choice_identifier"] = forms.ChoiceField(
            choices=_get_service_choices(self.service_provider),
            required=bool(self.service_provider),
            label=_("Service"),
        )


def _get_service_choices(service_provider):
    if not service_provider:
        return []
    service_choices = service_provider.get_service_choices()
    return [("", "---------")] + [(sc.identifier, sc.name) for sc in service_choices]


class ShippingMethodForm(BaseMethodForm):
    class Meta(BaseMethodForm.Meta):
        model = ShippingMethod
        fields = [
            "name", "description", "enabled", "shop", "logo", "carrier",
            "choice_identifier", "tax_class",
        ]

    @property
    def service_provider(self):
        return self.instance.carrier if self.instance.pk else None


class PaymentMethodForm(BaseMethodForm):
    class Meta(BaseMethodForm.Meta):
        model = PaymentMethod
        fields = [
            "name", "description", "enabled", "shop", "logo", "payment_processor",
            "choice_identifier", "tax_class",
        ]

    @property
    def service_provider(self):
        return self.instance.payment_processor if self.instance.pk else None


class FixedCostBehaviorComponentForm(ShoopAdminForm):
    class Meta:
        model = FixedCostBehaviorComponent
        exclude = ["identifier"]
        labels = {
            "price_value": _("Price"),
        }


class WaivingCostBehaviorComponentForm(ShoopAdminForm):
    class Meta:
        model = WaivingCostBehaviorComponent
        exclude = ["identifier"]
        labels = {
            "price_value": _("Price"),
            "waive_limit_value": _("Waive limit")
        }


class WeightLimitsBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = WeightLimitsBehaviorComponent
        exclude = ["identifier"]
