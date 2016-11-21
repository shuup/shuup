# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.forms import ShuupAdminForm
from shuup.admin.views.wizard import TemplatedWizardFormDef
from shuup.core.models import (
    CustomCarrier, CustomPaymentProcessor, Shop, TaxClass
)


class CustomCarrierForm(ShuupAdminForm):
    class Meta:
        model = CustomCarrier
        exclude = ("identifier", )


class CustomPaymentProcessorForm(ShuupAdminForm):
    class Meta:
        model = CustomPaymentProcessor
        exclude = ("identifier", )


class ServiceWizardForm(ShuupAdminForm):
    def get_service_choice(self, provider):
        return provider.get_service_choices()[0]

    def save(self):
        is_new = not self.instance.pk
        provider = super(ServiceWizardForm, self).save()
        provider.enabled = True
        provider.save()
        if is_new:
            service_choice = self.get_service_choice(provider)
            provider.create_service(
                service_choice,
                name=self.cleaned_data.get("service_name", service_choice.name),
                description=self.cleaned_data.get("service_description", ""),
                shop=Shop.objects.first(),
                tax_class=TaxClass.objects.first(),
                enabled=True
            )
        return provider


class ServiceWizardFormDef(TemplatedWizardFormDef):
    priority = 0

    def __init__(self, name, form_class, template_name, extra_js="", kwargs={}):
        kwargs.update({
            "instance": form_class._meta.model.objects.first(),
            "languages": configuration.get(Shop.objects.first(), "languages", settings.LANGUAGES)
        })
        form_def_kwargs = {
            "name": name,
            "kwargs": kwargs
        }
        super(ServiceWizardFormDef, self).__init__(
            form_class=form_class,
            template_name=template_name,
            extra_js=extra_js,
            **form_def_kwargs
        )

    def visible(self):
        return True


class ManualShippingWizardForm(ServiceWizardForm):
    service_name = forms.CharField(label=_("Service name"), help_text=_("The name shown in the shop checkout process."))
    service_description = forms.CharField(label=_("Instructions"),
                                          required=False,
                                          widget=forms.Textarea,
                                          help_text=_("additional instructions shown in the shop checkout process."))

    class Meta:
        model = CustomCarrier
        fields = ("name",)


class ManualShippingWizardFormDef(ServiceWizardFormDef):
    priority = 1000

    def __init__(self):
        super(ManualShippingWizardFormDef, self).__init__(
            name="manual_shipping",
            form_class=ManualShippingWizardForm,
            template_name="shuup/admin/service_providers/_wizard_manual_shipping_form.jinja"
        )


class ManualPaymentWizardForm(ServiceWizardForm):
    service_name = forms.CharField(label=_("Service name"), help_text=_("The name shown in the shop checkout process."))
    service_description = forms.CharField(label=_("Instructions"),
                                          required=False,
                                          widget=forms.Textarea,
                                          help_text=_("additional instructions shown in the shop checkout process."))

    class Meta:
        model = CustomPaymentProcessor
        fields = ("name",)


class ManualPaymentWizardFormDef(ServiceWizardFormDef):
    priority = 1000

    def __init__(self):
        super(ManualPaymentWizardFormDef, self).__init__(
            name="manual_payment",
            form_class=ManualPaymentWizardForm,
            template_name="shuup/admin/service_providers/_wizard_manual_payment_form.jinja"
        )
