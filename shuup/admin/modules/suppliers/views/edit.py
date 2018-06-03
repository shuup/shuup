# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.views import (
    check_and_raise_if_only_one_allowed, CreateOrUpdateView
)
from shuup.core.models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        exclude = ("module_data",)
        widgets = {
            "module_identifier": forms.Select
        }

    def save(self, commit=True):
        instance = super(SupplierForm, self).save(commit)
        instance.shop_products.remove(
            *list(instance.shop_products.exclude(shop_id__in=instance.shops.all()).values_list("pk", flat=True)))
        return instance


class SupplierEditView(CreateOrUpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "shuup/admin/suppliers/edit.jinja"
    context_object_name = "supplier"

    def get_object(self, queryset=None):
        obj = super(SupplierEditView, self).get_object(queryset)
        check_and_raise_if_only_one_allowed("SHUUP_ENABLE_MULTIPLE_SUPPLIERS", obj)
        return obj

    def get_form(self, form_class=None):
        form = super(SupplierEditView, self).get_form(form_class=form_class)
        choices = self.model.get_module_choices(
            empty_label=(_("No %s module") % self.model._meta.verbose_name)
        )
        form.fields["module_identifier"].choices = form.fields["module_identifier"].widget.choices = choices
        return form
