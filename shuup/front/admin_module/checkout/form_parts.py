# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.front.checkout.methods import PAYMENT_METHOD_REQUIRED_CONFIG_KEY, SHIPPING_METHOD_REQUIRED_CONFIG_KEY


class CheckoutConfigurationForm(forms.Form):
    shipping_method_required = forms.BooleanField(
        required=False,
        label=_("Require shipping method"),
        help_text=_("Whether to require the shipping method in checkout phases."),
    )
    payment_method_required = forms.BooleanField(
        required=False,
        label=_("Require payment method"),
        help_text=_("Whether to require the payment method in checkout phases."),
    )


class CheckoutShopFormPart(FormPart):
    priority = 8
    name = "checkout_config"
    form = CheckoutConfigurationForm

    def get_form_defs(self):
        if not self.object.pk:
            return
        initial = {
            "shipping_method_required": configuration.get(self.object, SHIPPING_METHOD_REQUIRED_CONFIG_KEY, True),
            "payment_method_required": configuration.get(self.object, PAYMENT_METHOD_REQUIRED_CONFIG_KEY, True),
        }
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shuup/front/admin/checkout.jinja",
            required=True,
            kwargs={"initial": initial},
        )

    def form_valid(self, form):
        if self.name not in form.forms:
            return
        data = form.forms[self.name].cleaned_data
        configuration.set(self.object, SHIPPING_METHOD_REQUIRED_CONFIG_KEY, data.get("shipping_method_required", False))
        configuration.set(self.object, PAYMENT_METHOD_REQUIRED_CONFIG_KEY, data.get("payment_method_required", False))
