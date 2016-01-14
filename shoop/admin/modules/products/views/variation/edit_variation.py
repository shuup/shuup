# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView

from shoop.admin.base import MenuEntry
from shoop.admin.form_part import (
    FormPart, FormPartsViewMixin, TemplatedFormDef
)
from shoop.admin.toolbar import (
    get_default_edit_toolbar, PostActionButton, Toolbar
)
from shoop.admin.utils.urls import get_model_url
from shoop.core.models import Product, ProductMode, ProductVariationVariable
from shoop.utils.excs import Problem

from .simple_variation_forms import (
    SimpleVariationChildForm, SimpleVariationChildFormSet
)
from .variable_variation_forms import (
    VariableVariationChildrenForm, VariationVariablesDataForm
)


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
            kwargs={"parent_product": product, "request": self.request}
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


class ProductVariationViewToolbar(Toolbar):
    def __init__(self, view):
        super(ProductVariationViewToolbar, self).__init__()
        self.view = view
        self.parent_product = view.object
        self.request = view.request
        get_default_edit_toolbar(self.view, "product_form", with_split_save=False, toolbar=self)

        if self.parent_product.variation_children.exists():
            self.append(PostActionButton(
                post_url=self.request.path,
                name="command",
                value="unvariate",
                confirm=_("Are you sure? This will unlink all children and remove all variation variables."),
                text=_("Clear variation"),
                extra_css_class="btn-danger",
                icon="fa fa-times"
            ))
        if (
            self.parent_product.mode == ProductMode.VARIABLE_VARIATION_PARENT or
            ProductVariationVariable.objects.filter(product=self.parent_product).exists()
        ):
            self.append(PostActionButton(
                post_url=self.request.path,
                name="command",
                value="simplify",
                confirm=_("Are you sure? This will remove all variation variables, "
                          "converting children to direct links."),
                text=_("Convert to simple variation"),
                icon="fa fa-exchange",
                extra_css_class="btn-info"
            ))


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

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=self.object,
                url=get_model_url(self.object)
            )
        ]

    def post(self, request, *args, **kwargs):
        command = request.POST.get("command")
        if command:
            return self.dispatch_command(request, command)
        return super(ProductVariationView, self).post(request, *args, **kwargs)

    def get_form_part_classes(self):
        yield VariationChildrenFormPart
        yield VariationVariablesFormPart

    def get_context_data(self, **kwargs):
        context = super(ProductVariationView, self).get_context_data(**kwargs)
        context["toolbar"] = ProductVariationViewToolbar(self)
        context["title"] = _("Edit Variation: %s") % self.object
        context["is_variation"] = self.object.is_variation_parent()
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

    def dispatch_command(self, request, command):
        product = self.object
        if command == "unvariate":
            product.clear_variation()
            messages.success(self.request, _("Variation cleared."))
        elif command == "simplify":
            product.simplify_variation()
            messages.success(self.request, _("Variation simplified."))
        else:
            raise Problem("Unknown command: %s" % command)
        return HttpResponseRedirect(self.get_success_url())
