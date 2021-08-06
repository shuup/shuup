# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod
from shuup.core.models import ConfigurationItem, Currency
from shuup.core.setting_keys import SHUUP_HOME_CURRENCY


class BaseSettingsFormPart(FormPart):
    name = "base_settings"
    form = None  # override in subclass

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.form,
            required=False,
            template_name="shuup/admin/settings/form_parts/settings_base.jinja",
            kwargs={"request": self.request},
        )

    def save(self, form):
        if not form.has_changed():
            return False  # no need to save

        for key in form.fields.keys():
            try:
                ConfigurationItem.objects.get(shop=None, key=key).delete()
            except ConfigurationItem.DoesNotExist:
                continue

        for key, value in six.iteritems(form.cleaned_data):
            if isinstance(value, Enum):
                value = value.value
            if isinstance(value, models.Model):
                value = str(value)
            configuration.set(None, key, value)
        return True


class BaseSettingsForm(forms.Form):
    title = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(BaseSettingsForm, self).__init__(*args, **kwargs)

        for field in self.fields.keys():
            self.fields[field].initial = configuration.get(None, field)


class OrderSettingsForm(BaseSettingsForm):
    title = _("Order Settings")
    order_reference_number_method = EnumField(OrderReferenceNumberMethod).formfield(
        label=_("Order Reference number method"),
        help_text=_(
            "This option defines how the reference numbers for orders are built. The options are:"
            "<br><br><b>Unique</b><br>Order reference number is unique system wide, "
            "regardless of the amount of shops."
            "<br><br><b>Running</b><br>Order number is running system wide, regardless of the amount of shops."
            "<br><br><b>Shop Running</b><br>Every shop has its own running numbers for reference."
        ),
        required=False,
    )


class OrderSettingsFormPart(BaseSettingsFormPart):
    form = OrderSettingsForm
    name = "order_settings"


class CoreSettingsForm(BaseSettingsForm):
    title = _("Core Settings")
    home_currency = forms.ModelChoiceField(
        label=_("Home Currency"),
        queryset=Currency.objects.all(),
        help_text=_(
            "This option defines the currency in that all the monetary values are expressed. "
            "Enter a valid ISO-4217 currency code."
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super(CoreSettingsForm, self).__init__(*args, **kwargs)
        self.fields[SHUUP_HOME_CURRENCY].initial = Currency.objects.filter(
            code=configuration.get(None, SHUUP_HOME_CURRENCY)
        ).first()


class CoreSettingsFormPart(BaseSettingsFormPart):
    form = CoreSettingsForm
    name = "core_settings"
