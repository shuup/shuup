# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from django.conf import settings

from shuup.admin.form_part import (
    FormPart, FormPartsViewMixin, SaveFormPartsMixin, TemplatedFormDef
)
from shuup.admin.forms.widgets import MediaChoiceWidget
from shuup.admin.utils.forms import filter_form_field_choices
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Category, CategoryStatus
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class CategoryBaseForm(MultiLanguageModelForm):
    class Meta:
        model = Category
        fields = (
            "parent",
            "shops",
            "status",
            "ordering",
            "visibility",
            "visibility_groups",
            "name",
            "image",
            "description",
            "slug",
        )

        widgets = {
            "status": forms.RadioSelect,
            "visibility": forms.RadioSelect,
        }

    def __init__(self, **kwargs):
        super(CategoryBaseForm, self).__init__(**kwargs)
        # Exclude `DELETED`. We don't want people to use that field to set a category as deleted.
        filter_form_field_choices(self.fields["status"], (CategoryStatus.DELETED.value,), invert=True)

        # Exclude current category from parents, because it cannot be its own child anyways
        filter_form_field_choices(self.fields["parent"], (kwargs["instance"].pk,), invert=True)
        self.fields["image"].widget = MediaChoiceWidget(clearable=True)


class CategoryBaseFormPart(FormPart):
    priority = -1000  # Show this first, no matter what

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            CategoryBaseForm,
            template_name="shuup/admin/categories/_edit_base_form.jinja",
            required=True,
            kwargs={"instance": self.object, "languages": settings.LANGUAGES}
        )

    def form_valid(self, form):
        rebuild = ("parent" in form["base"].changed_data)
        self.object = form["base"].save()
        if rebuild:
            Category.objects.rebuild()


class CategoryEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Category
    template_name = "shuup/admin/categories/edit.jinja"
    context_object_name = "category"
    base_form_part_classes = [CategoryBaseFormPart]
    form_part_class_provide_key = "admin_category_form_part"

    def form_valid(self, form):
        return self.save_form_parts(form)
