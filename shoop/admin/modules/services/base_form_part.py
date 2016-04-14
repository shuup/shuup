# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.conf import settings

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.admin.modules.services.forms import (
    PaymentMethodForm, ShippingMethodForm
)


class ServiceBaseFormPart(FormPart):
    priority = -1000  # Show this first
    form = None  # Override in subclass

    def __init__(self, *args, **kwargs):
        super(ServiceBaseFormPart, self).__init__(*args, **kwargs)

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            self.form,
            required=True,
            template_name="shoop/admin/services/_edit_base_form.jinja",
            kwargs={"instance": self.object, "languages": settings.LANGUAGES}
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object


class ShippingMethodBaseFormPart(ServiceBaseFormPart):
    form = ShippingMethodForm


class PaymentMethodBaseFormPart(ServiceBaseFormPart):
    form = PaymentMethodForm
