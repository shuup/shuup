# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef

CART_UPDATE_DELAY_CONF_KEY = "shuup_front_cart_update_delay"

class CartDelayConfigurationForm(forms.Form):
    shuup_front_cart_update_delay = forms.IntegerField(
        required=True,
        initial=2,
        min_value=0,
        label=_("Cart Inactivity Delay (hours)"),
        help_text=_("Set the number of hours the cart must be inactive before it's displayed in Orders > Carts")
    )


class CartDelayFormPart(FormPart):
    priority = 8
    name = "cart_delay"
    form = CartDelayConfigurationForm

    def get_form_defs(self):
        if not self.object.pk:
            return
        initial = {
            CART_UPDATE_DELAY_CONF_KEY: configuration.get(self.object, CART_UPDATE_DELAY_CONF_KEY, 0)
        }
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shuup/front/admin/cart_delay.jinja",
            required=False,
            kwargs={"initial": initial}
        )

    def form_valid(self, form):
        if self.name not in form.forms:
            return
        data = form.forms[self.name].cleaned_data
        configuration.set(self.object, CART_UPDATE_DELAY_CONF_KEY, data.get(CART_UPDATE_DELAY_CONF_KEY, 2))
