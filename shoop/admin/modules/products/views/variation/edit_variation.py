# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django import forms
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView
from shoop.admin.form_part import FormPartsViewMixin, FormPart, TemplatedFormDef
from shoop.admin.toolbar import get_default_edit_toolbar
from shoop.core.models import Product, ProductMode
from .simple_variation_forms import SimpleVariationChildForm, SimpleVariationChildFormSet
from .variable_variation_forms import VariableVariationChildrenForm, VariationVariablesDataForm


class VariationChildrenFormPart(FormPart):
    priority = 0

    def get_form_defs(self):
        product = self.object
        if product.mode == ProductMode.VARIATION_CHILD:
            raise ValueError("Invalid mode")
        elif product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            form = VariableVariationChildrenForm
            template_name = "shoop/admin/products/variation/_variable_variation_children.jinja"
        else:
            form = formset_factory(SimpleVariationChildForm, SimpleVariationChildFormSet, extra=5, can_delete=True)
            template_name = "shoop/admin/products/variation/_simple_variation_children.jinja"

        yield TemplatedFormDef(
            "children",
            form,
            template_name=template_name,
            required=False,
            kwargs={"parent_product": product}
        )

    def form_valid(self, form):
        try:
            children_formset = form["children"]
        except KeyError:
            return
        children_formset.save()


class VariationVariablesFormPart(FormPart):
    priority = 1

    def get_form_defs(self):
        yield TemplatedFormDef(
            "variables",
            VariationVariablesDataForm,
            template_name="shoop/admin/products/variation/_variation_variables.jinja",
            required=False,
            kwargs={"parent_product": self.object}
        )

    def form_valid(self, form):
        try:
            var_form = form["variables"]
        except KeyError:
            return
        var_form.save()


class ProductVariationView(FormPartsViewMixin, UpdateView):
    model = Product
    template_name = "shoop/admin/products/variation/edit.jinja"
    context_object_name = "product"
    form_class = forms.Form

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.variation_parent_id:
            # Redirect to the parent instead.
            return HttpResponseRedirect(
                reverse("shoop_admin:product.edit_variation", kwargs={"pk": self.object.variation_parent_id})
            )
        return super(ProductVariationView, self).dispatch(request, *args, **kwargs)

    def get_form_part_classes(self):
        yield VariationChildrenFormPart
        yield VariationVariablesFormPart

    def get_context_data(self, **kwargs):
        context = super(ProductVariationView, self).get_context_data(**kwargs)
        context["toolbar"] = get_default_edit_toolbar(self, "product_form", with_split_save=False)
        context["title"] = _("Edit Variation: %s") % self.object
        return context

    def form_valid(self, form):
        form_parts = self.get_form_parts(self.object)
        for form_part in form_parts:
            form_part.form_valid(form)
        self.object.verify_mode()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.request.path
