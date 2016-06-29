# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms

from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import ProductType
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


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
    template_name = "shuup/admin/product_types/edit.jinja"
    context_object_name = "product_type"
