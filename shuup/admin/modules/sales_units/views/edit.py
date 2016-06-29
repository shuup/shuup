# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import SalesUnit
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
