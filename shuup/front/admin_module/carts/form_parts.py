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
CART_UPDATE_DELAY_DEFAULT = 2


def get_cart_delay_hours(shop):
    return configuration.get(shop, CART_UPDATE_DELAY_CONF_KEY, CART_UPDATE_DELAY_DEFAULT)


def set_cart_delay_hours(shop, value):
    return configuration.set(
        shop,
        CART_UPDATE_DELAY_CONF_KEY,
        (value or CART_UPDATE_DELAY_DEFAULT)
    )


class CartDelayConfigurationForm(forms.Form):
    shuup_front_cart_update_delay = forms.IntegerField(
        required=False,
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

        initial = {"shuup_front_cart_update_delay":  get_cart_delay_hours(self.object)}
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
        set_cart_delay_hours(self.object, data.get("shuup_front_cart_update_delay"))
