# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django_countries import Countries

from shuup.admin.forms import ShuupAdminForm
from shuup.admin.forms.widgets import (
    QuickAddLabelMultiSelect, TextEditorWidget
)
from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.core.models import (
    Carrier, CountryLimitBehaviorComponent, FixedCostBehaviorComponent,
    GroupAvailabilityBehaviorComponent, OrderTotalLimitBehaviorComponent,
    PaymentMethod, PaymentProcessor, ServiceProvider, ShippingMethod,
    StaffOnlyBehaviorComponent, WaivingCostBehaviorComponent,
    WeightLimitsBehaviorComponent
)


def get_service_providers_filters(request, payment_method=None):
    shop_filter = Q(
        Q(shops__isnull=True) |
        Q(shops=get_shop(request))
    )
    if payment_method and payment_method.pk and payment_method.supplier:
        return shop_filter & Q(
            Q(supplier__isnull=True) |
            Q(supplier=get_supplier(request)) |
            Q(supplier=payment_method.supplier)
        )

    return shop_filter & Q(
        Q(supplier__isnull=True) |
        Q(supplier=get_supplier(request))
    )


class BaseMethodForm(ShuupAdminForm):
    class Meta:
        model = None
        exclude = [
            "identifier", "behavior_components", "old_module_identifier",
            "old_module_data", "shop"
        ]
        base_fields = [
            "choice_identifier", "name", "description", "enabled",
            "logo", "tax_class", "labels", "supplier"
        ]
        widgets = {
            "description": TextEditorWidget(),
            "labels": QuickAddLabelMultiSelect(),
        }

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
            help_text=_("Select a service to use for this service provider.")
        )
        self.fields[self.service_provider_attr].required = True

    def get_service_provider(self, id):
        if not id:
            return
        return ServiceProvider.objects.filter(
            get_service_providers_filters(self.request, self.instance)
        ).filter(pk=id).first()

    @property
    def service_provider(self):
        return getattr(self.instance, self.service_provider_attr) if self.instance else None

    @service_provider.setter
    def service_provider(self, value):
        setattr(self.instance, self.service_provider_attr, value)

    def _save_master(self, commit=True):
        self.cleaned_data['shop'] = self.request.shop
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


class AlwaysChangedModelForm(forms.ModelForm):
    """
    ModelForm that can be saved if it is empty or has unchanged lines on creation
    """
    def has_changed(self, *args, **kwargs):
        if self.instance.pk is None:
            return True
        return super(AlwaysChangedModelForm, self).has_changed(*args, **kwargs)


class ShippingMethodForm(BaseMethodForm):
    service_provider_attr = "carrier"

    class Meta(BaseMethodForm.Meta):
        model = ShippingMethod
        fields = ["carrier"] + BaseMethodForm.Meta.base_fields
        help_texts = {
            "carrier": _(
                "The carrier to use for this shipping method. "
                "Select a carrier before filling other fields."
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["carrier"].queryset = Carrier.objects.filter(
            get_service_providers_filters(self.request, self.instance)
        ).distinct()


class PaymentMethodForm(BaseMethodForm):
    service_provider_attr = "payment_processor"

    class Meta(BaseMethodForm.Meta):
        model = PaymentMethod
        fields = ["payment_processor"] + BaseMethodForm.Meta.base_fields
        help_texts = {
            "payment_processor": _(
                "The payment processor to use for this payment method. "
                "Select a payment processor before filling out the other fields."
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_processor"].queryset = PaymentProcessor.objects.filter(
            get_service_providers_filters(self.request, self.instance)
        ).distinct()


class FixedCostBehaviorComponentForm(ShuupAdminForm):
    class Meta:
        model = FixedCostBehaviorComponent
        exclude = ["identifier"]
        labels = {
            "price_value": _("Price"),
        }


class WaivingCostBehaviorComponentForm(ShuupAdminForm):
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


class GroupAvailabilityBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = GroupAvailabilityBehaviorComponent
        exclude = ["identifier"]


class StaffOnlyBehaviorComponentForm(AlwaysChangedModelForm):
    class Meta:
        model = StaffOnlyBehaviorComponent
        exclude = ["identifier"]


class OrderTotalLimitBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = OrderTotalLimitBehaviorComponent
        exclude = ["identifier"]


class CountryLimitBehaviorComponentForm(forms.ModelForm):
    available_in_countries = forms.MultipleChoiceField(
        choices=Countries, label=_("Available in countries"), required=False)
    unavailable_in_countries = forms.MultipleChoiceField(
        choices=Countries, label=_("Unavailable in countries"), required=False)

    class Meta:
        model = CountryLimitBehaviorComponent
        exclude = ["identifier"]
        help_texts = {
            "available_in_countries": _("Select accepted countries for this service."),
            "available_in_european_countries": _("Select this to accept all countries in EU."),
            "unavailable_in_countries": _("Select restricted countries for this service."),
            "unavailable_in_european_countries": _("Select this to restrict this service for countries in EU")
        }

    def __init__(self, **kwargs):
        super(CountryLimitBehaviorComponentForm, self).__init__(**kwargs)
        if self.instance and self.instance.pk:
            self.initial["available_in_countries"] = self.instance.available_in_countries
            self.initial["unavailable_in_countries"] = self.instance.unavailable_in_countries
