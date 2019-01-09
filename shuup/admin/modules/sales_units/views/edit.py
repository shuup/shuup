# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import DisplayUnit, SalesUnit
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class SalesUnitForm(MultiLanguageModelForm):
    class Meta:
        model = SalesUnit
        exclude = ()  # All the fields!


class SalesUnitEditView(CreateOrUpdateView):
    model = SalesUnit
    form_class = SalesUnitForm
    template_name = "shuup/admin/sales_units/edit.jinja"
    context_object_name = "sales_unit"


class DisplayUnitForm(MultiLanguageModelForm):
    class Meta:
        model = DisplayUnit
        exclude = ()  # All the fields!


class DisplayUnitEditView(CreateOrUpdateView):
    model = DisplayUnit
    form_class = DisplayUnitForm
    template_name = "shuup/admin/sales_units/edit_display_unit.jinja"
    context_object_name = "display_unit"
