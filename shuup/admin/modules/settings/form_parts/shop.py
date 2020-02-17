# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal

import babel.core
import six
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_MAX_DIGITS, FormattedDecimalFormField
)
from shuup.core.models import ConfigurationItem
from shuup.core.order_creator.constants import ORDER_MIN_TOTAL_CONFIG_KEY


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

        decimal_places = 2  # default
        if shop.currency in babel.core.get_global('currency_fractions'):
            decimal_places = babel.core.get_global('currency_fractions')[shop.currency][0]

        self.fields[ORDER_MIN_TOTAL_CONFIG_KEY] = FormattedDecimalFormField(
            label=_("Order minimum total"),
            decimal_places=decimal_places,
            max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
            min_value=0,
            required=False,
            initial=configuration.get(shop, ORDER_MIN_TOTAL_CONFIG_KEY, Decimal(0)),
            help_text=_("The minimum sum that an order needs to reach to be created.")
        )


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
            if not used_form.has_changed():
                return None  # no need to save

            for key in used_form.fields.keys():
                try:
                    ConfigurationItem.objects.get(shop=self.object, key=key).delete()
                except ConfigurationItem.DoesNotExist:
                    continue

            for key, value in six.iteritems(used_form.cleaned_data):
                configuration.set(shop=self.object, key=key, value=value)
