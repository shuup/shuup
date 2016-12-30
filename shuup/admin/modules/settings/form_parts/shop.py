# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.models import ConfigurationItem


class ShopOrderConfigurationForm(forms.Form):
    order_reference_number_length = forms.IntegerField(
        label=_("Reference number length"),
        initial=29,
        min_value=17,
        max_value=69,
        help_text=_("Length of the order reference number not including the checksum number. "
                    "This can vary based on the country your shop is in. "
                    "If you set the length to 19, the actual length is going to be 20 "
                    "because the checksum is being added."),
    )

    order_reference_number_prefix = forms.IntegerField(label=_("Reference number prefix"), required=False)

    def __init__(self, *args, **kwargs):
        from shuup.admin.modules.settings import consts
        from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod
        shop = kwargs.pop("shop")
        kwargs["initial"] = {
            consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD: configuration.get(
                shop, consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD, settings.SHUUP_REFERENCE_NUMBER_LENGTH),
            consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD: configuration.get(
                shop, consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD, settings.SHUUP_REFERENCE_NUMBER_PREFIX),
        }
        super(ShopOrderConfigurationForm, self).__init__(*args, **kwargs)

        reference_method = configuration.get(
            shop, consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD, settings.SHUUP_REFERENCE_NUMBER_METHOD)

        self.prefix_disabled = (reference_method in
                                [OrderReferenceNumberMethod.UNIQUE.value,
                                 OrderReferenceNumberMethod.SHOP_RUNNING.value])

        self.fields[consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD].disabled = self.prefix_disabled


class OrderConfigurationFormPart(FormPart):
    priority = 7
    name = "order_configuration"
    form = ShopOrderConfigurationForm

    def get_form_defs(self):
        if not self.object.pk:
            return

        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shuup/admin/settings/form_parts/shop.jinja",
            required=False,
            kwargs={"shop": self.object}
        )

    def form_valid(self, form):
        if self.name in form.forms:
            used_form = form[self.name]
            for key in used_form.fields.keys():
                try:
                    ConfigurationItem.objects.get(shop=self.object, key=key).delete()
                except ConfigurationItem.DoesNotExist:
                    continue

            for key, value in six.iteritems(used_form.cleaned_data):
                configuration.set(shop=self.object, key=key, value=value)
