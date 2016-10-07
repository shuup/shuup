# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.apps.provides import get_provide_objects
from shuup.core.models import PaymentMethod, ShippingMethod


class ServiceProviderTypeForm(forms.Form):
    providers = forms.CharField(label=_("Provider"), required=False)


class ServiceWizardFormPartMixin(object):
    def visible(self):
        return not self.service_model.objects.for_shop(shop=self.object).exists()

    def _get_service_provider_form_defs(self):
        form_defs = []
        for form_def in get_provide_objects(self.form_def_provide_key):
            form_defs.append(form_def())
        form_defs.sort(key=lambda form_def: getattr(form_def, "priority", 0))
        return form_defs

    def get_form_defs(self):
        service_provider_form_defs = self._get_service_provider_form_defs()

        if self.request.method == "POST":
            active_providers = self.request.POST.get(self.base_name + "-providers").split(",")
            service_provider_form_defs = list(
                filter(
                    lambda x: x.name in active_providers,
                    service_provider_form_defs
                )
            )
        return [
            TemplatedWizardFormDef(
                name=self.base_name,
                template_name="shuup/admin/service_providers/_wizard_service_provider_base_form.jinja",
                extra_js="shuup/admin/service_providers/_wizard_script.jinja",
                form_class=ServiceProviderTypeForm,
            )
        ] + service_provider_form_defs

    def form_valid(self, form):
        providers = form[self.base_name].cleaned_data.get("providers").split(",")
        for provider in providers:
            provider_form = form.forms.get(provider, None)
            if provider_form:
                form[provider].save()


class CarrierWizardPane(ServiceWizardFormPartMixin, WizardPane):
    identifier = "carrier"
    text = _("Please add shipping methods for your shop")
    icon = "shuup_admin/img/shipping.png"
    service_model = ShippingMethod
    base_name = "shipping_method_base"
    provider_label = _("Carrier")
    form_def_provide_key = "carrier_wizard_form_def"


class PaymentWizardPane(ServiceWizardFormPartMixin, WizardPane):
    identifier = "payment"
    title = _("Payment Methods")
    text = _("Please add payment methods for your shop")
    icon = "shuup_admin/img/payment.png"
    service_model = PaymentMethod
    base_name = "payment_method_base"
    provider_label = _("Payment Processor")
    form_def_provide_key = "payment_processor_wizard_form_def"
