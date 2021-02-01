# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings

from shuup import configuration
from shuup.admin.views.wizard import TemplatedWizardFormDef

from .wizard_forms import ManualPaymentWizardForm, ManualShippingWizardForm


class ServiceWizardFormDef(TemplatedWizardFormDef):
    priority = 0

    def __init__(self, name, form_class, template_name, request, extra_js=""):
        shop = request.shop
        form_def_kwargs = {
            "name": name,
            "kwargs": {
                "instance": form_class._meta.model.objects.first(),
                "languages": configuration.get(shop, "languages", settings.LANGUAGES)
            }
        }
        super(ServiceWizardFormDef, self).__init__(
            form_class=form_class,
            template_name=template_name,
            extra_js=extra_js,
            **form_def_kwargs
        )

    def visible(self):
        return True


class ManualShippingWizardFormDef(ServiceWizardFormDef):
    priority = 1000

    def __init__(self, request):
        super(ManualShippingWizardFormDef, self).__init__(
            name="manual_shipping",
            form_class=ManualShippingWizardForm,
            template_name="shuup/admin/service_providers/_wizard_manual_shipping_form.jinja",
            request=request
        )


class ManualPaymentWizardFormDef(ServiceWizardFormDef):
    priority = 1000

    def __init__(self, request):
        super(ManualPaymentWizardFormDef, self).__init__(
            name="manual_payment",
            form_class=ManualPaymentWizardForm,
            template_name="shuup/admin/service_providers/_wizard_manual_payment_form.jinja",
            request=request
        )
