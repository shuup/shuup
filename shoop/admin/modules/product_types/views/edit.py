# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals
from django import forms
from shoop.admin.utils.views import CreateOrUpdateView, add_create_or_change_message
from shoop.core.models.products import ProductType
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class ProductTypeForm(MultiLanguageModelForm):
    class Meta:
        model = ProductType
        exclude = ()  # All the fields!
        widgets = {
            "attributes": forms.CheckboxSelectMultiple
        }


class ProductTypeEditView(CreateOrUpdateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = "shoop/admin/product_types/edit.jinja"
    context_object_name = "product_type"

    def form_valid(self, form):
        is_new = (not self.object.pk)
        add_create_or_change_message(self.request, self.object, is_new=is_new)
        return super(ProductTypeEditView, self).form_valid(form)
