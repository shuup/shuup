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
    FixedCostBehaviorComponent, PaymentMethod, ServiceProvider, ShippingMethod,
    WaivingCostBehaviorComponent, WeightLimitsBehaviorComponent
)


class BaseMethodForm(ShoopAdminForm):
    class Meta:
        model = None
        exclude = [
            "identifier", "behavior_components", "old_module_identifier",
            "old_module_data"
        ]
        base_fields = [
            "choice_identifier", "name", "description", "enabled", "shop",
            "logo", "tax_class"
        ]

    def __init__(self, **kwargs):
        self.request = kwargs.pop("request")
        self.instance = kwargs.get("instance")
        selected_provider = self.get_service_provider(self.request.GET.get("provider"))
        if selected_provider:
            self.service_provider = selected_provider
        super(BaseMethodForm, self).__init__(**kwargs)
        self.fields["choice_identifier"] = forms.ChoiceField(
            choices=_get_service_choices(self.service_provider),
            required=bool(self.service_provider),
            label=_("Service"),
        )
        self.fields[self.service_provider_attr].required = True

    def get_service_provider(self, id):
        if not id:
            return
        return ServiceProvider.objects.filter(id=id).first()

    @property
    def service_provider(self):
        return getattr(self.instance, self.service_provider_attr) if self.instance else None

    @service_provider.setter
    def service_provider(self, value):
        setattr(self.instance, self.service_provider_attr, value)

    def _save_master(self, commit=True):
        if self.instance.pk:
            return super(BaseMethodForm, self)._save_master(commit)

        # New services are always created with provider.create_service method
        service_data = self._get_cleaned_data_without_translations()
        provider = service_data.pop(self.service_provider_attr)
        choice_identifier = service_data.pop("choice_identifier")

        return provider.create_service(choice_identifier, **service_data)


def _get_service_choices(service_provider):
    if not service_provider:
        return []
    service_choices = service_provider.get_service_choices()
    return [(sc.identifier, sc.name) for sc in service_choices]


class ShippingMethodForm(BaseMethodForm):
    service_provider_attr = "carrier"

    class Meta(BaseMethodForm.Meta):
        model = ShippingMethod
        fields = ["carrier"] + BaseMethodForm.Meta.base_fields
        help_texts = {
            "carrier": _("Select carrier before filling other fields.")
        }


class PaymentMethodForm(BaseMethodForm):
    service_provider_attr = "payment_processor"

    class Meta(BaseMethodForm.Meta):
        model = PaymentMethod
        fields = ["payment_processor"] + BaseMethodForm.Meta.base_fields
        help_texts = {
            "payment_processor": _("Select payment processor before filling other fields.")
        }


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
