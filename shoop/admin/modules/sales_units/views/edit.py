# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals
from shoop.admin.utils.views import CreateOrUpdateView, add_create_or_change_message
from shoop.core.models import SalesUnit
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class SalesUnitForm(MultiLanguageModelForm):
    class Meta:
        model = SalesUnit
        exclude = ()  # All the fields!


class SalesUnitEditView(CreateOrUpdateView):
    model = SalesUnit
    form_class = SalesUnitForm
    template_name = "shoop/admin/sales_units/edit.jinja"
    context_object_name = "sales_unit"

    def form_valid(self, form):
        is_new = (not self.object.pk)
        add_create_or_change_message(self.request, self.object, is_new=is_new)
        return super(SalesUnitEditView, self).form_valid(form)
