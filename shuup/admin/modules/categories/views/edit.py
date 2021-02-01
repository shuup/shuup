# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.modules.categories.form_parts import (
    CategoryBaseFormPart, CategoryProductFormPart
)
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.tour import is_tour_complete
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Category
from shuup.utils.django_compat import reverse_lazy


class CategoryEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Category
    template_name = "shuup/admin/categories/edit.jinja"
    context_object_name = "category"
    base_form_part_classes = [CategoryBaseFormPart, CategoryProductFormPart]
    form_part_class_provide_key = "admin_category_form_part"

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        object = self.get_object()
        delete_url = reverse_lazy("shuup_admin:category.delete", kwargs={"pk": object.pk}) if object.pk else None
        return get_default_edit_toolbar(self, save_form_id, delete_url=delete_url)

    def get_context_data(self, **kwargs):
        context = super(CategoryEditView, self).get_context_data(**kwargs)
        context["tour_key"] = "category"
        context["tour_complete"] = is_tour_complete(get_shop(self.request), "category", user=self.request.user)
        if self.object.pk:
            context["title"] = self.object.name

        return context

    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_queryset(self):
        return Category.objects.all_except_deleted(shop=get_shop(self.request))
