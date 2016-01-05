# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        exclude = ("module_data",)
        widgets = {
            "module_identifier": forms.Select
        }


class SupplierEditView(CreateOrUpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "shoop/admin/suppliers/edit.jinja"
    context_object_name = "supplier"

    def get_form(self, form_class=None):
        form = super(SupplierEditView, self).get_form(form_class=form_class)
        choices = self.model.get_module_choices(
            empty_label=(_("No %s module") % self.model._meta.verbose_name)
        )
        form.fields["module_identifier"].choices = form.fields["module_identifier"].widget.choices = choices
        return form
