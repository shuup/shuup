# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from enumfields import Enum

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.models import ConfigurationItem


class BaseSettingsFormPart(FormPart):
    name = "base_settings"
    form = None  # override in subclass

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.form,
            required=False,
            template_name="shuup/front/admin/settings_base.jinja",
            kwargs={"request": self.request}
        )

    def form_valid(self, form):
        if self.name not in form.forms:
            return

        form = form.forms[self.name]
        if not form.has_changed():
            return

        for key in form.fields.keys():
            try:
                ConfigurationItem.objects.get(shop=self.request.shop, key=key).delete()
            except ConfigurationItem.DoesNotExist:
                continue

        for key, value in six.iteritems(form.cleaned_data):
            if isinstance(value, Enum):
                value = value.value
            configuration.set(self.request.shop, key, value)


class BaseSettingsForm(forms.Form):
    title = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(BaseSettingsForm, self).__init__(*args, **kwargs)

        for field in self.fields.keys():
            self.fields[field].initial = configuration.get(self.request.shop, field)
