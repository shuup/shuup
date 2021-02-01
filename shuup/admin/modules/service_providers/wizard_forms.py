# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms import ShuupAdminForm
from shuup.core.models import (
    CustomCarrier, CustomPaymentProcessor, PaymentMethod, PaymentProcessor,
    ShippingMethod, TaxClass
)


class ServiceWizardForm(ShuupAdminForm):
    service_name = forms.CharField(
        label=_("Service name"), help_text=_("The name shown in the shop checkout process."))

    def __init__(self, **kwargs):
        self.provider = kwargs["instance"]
        super(ServiceWizardForm, self).__init__(**kwargs)

    def is_active(self):
        return bool(self.get_service()) if self.provider else None

    def get_service_choice(self, provider):
        return provider.get_service_choices()[0]

    def get_service(self):
        if issubclass(self.provider.__class__, PaymentProcessor):
            return self.get_payment_method()
        return self.get_shipping_method()

    def get_payment_method(self):
        return (PaymentMethod.objects.filter(payment_processor=self.provider).first() if self.provider else None)

    def get_shipping_method(self):
        return (ShippingMethod.objects.filter(carrier=self.provider).first() if self.provider else None)

    def save(self):
        is_new = not self.instance.pk
        provider = super(ServiceWizardForm, self).save()
        provider.enabled = True
        provider.save()
        if is_new:
            service_choice = self.get_service_choice(provider)
            shop = self.request.shop
            provider.create_service(
                service_choice,
                name=self.cleaned_data.get("service_name", service_choice.name),
                description=self.cleaned_data.get("service_description", ""),
                shop=shop,
                tax_class=TaxClass.objects.first(),
                enabled=True
            )
        else:
            service = self.get_service()
            if service:
                service.name = self.cleaned_data.get("service_name")
                service.description = self.cleaned_data.get("service_description", "")
                service.save()
        return provider


class ManualShippingWizardForm(ServiceWizardForm):
    service_description = forms.CharField(
        label=_("Instructions"), required=False, widget=forms.Textarea,
        help_text=_("Additional instructions shown in the shop checkout process."))

    def __init__(self, **kwargs):
        super(ManualShippingWizardForm, self).__init__(**kwargs)
        if not self.provider:
            return
        service = self.get_shipping_method()
        if not service:
            return
        self.fields["service_name"].initial = service.name
        self.fields["service_description"].initial = service.description

    class Meta:
        model = CustomCarrier
        fields = ("name",)


class ManualPaymentWizardForm(ServiceWizardForm):
    service_description = forms.CharField(
        label=_("Instructions"), required=False, widget=forms.Textarea,
        help_text=_("Additional instructions shown in the shop checkout process."))

    def __init__(self, **kwargs):
        super(ManualPaymentWizardForm, self).__init__(**kwargs)
        if not self.provider:
            return
        service = self.get_payment_method()
        if not service:
            return
        self.fields["service_name"].initial = service.name
        self.fields["service_description"].initial = service.description

    class Meta:
        model = CustomPaymentProcessor
        fields = ("name",)
