# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from shuup import configuration
from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod


class OrderSettingsForm(forms.Form):

    order_reference_number_method = EnumField(OrderReferenceNumberMethod).formfield(
        label=_("Order Reference number method"),
        help_text=_("This option defines how the reference numbers for orders are built. The options are:"
                    "<br><br><b>Unique</b><br>Order reference number is unique system wide, "
                    "regardless of the amount of shops."
                    "<br><br><b>Running</b><br>Order number is running system wide, regardless of the amount of shops."
                    "<br><br><b>Shop Running</b><br>Every shop has its own running numbers for reference."))

    def __init__(self, *args, **kwargs):
        super(OrderSettingsForm, self).__init__(*args, **kwargs)

        for field in self.fields.keys():
            self.fields[field].initial = configuration.get(None, field)
