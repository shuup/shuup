# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.modules.categories.form_parts import (
    CategoryBaseFormPart, CategoryProductFormPart
)
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Category


class CategoryEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Category
    template_name = "shuup/admin/categories/edit.jinja"
    context_object_name = "category"
    base_form_part_classes = [CategoryBaseFormPart, CategoryProductFormPart]
    form_part_class_provide_key = "admin_category_form_part"

    def form_valid(self, form):
        return self.save_form_parts(form)
