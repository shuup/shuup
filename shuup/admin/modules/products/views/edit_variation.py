# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.modules.products.forms import (
    SimpleVariationChildForm, SimpleVariationChildFormSet,
    VariableVariationChildrenForm, VariationVariablesDataForm
)
from shuup.admin.toolbar import PostActionButton
from shuup.core.models import ProductMode, ProductVariationVariable
from shuup.utils.excs import Problem

from .edit_parent import (
    ProductChildrenBaseFormPart, ProductParentBaseToolbar,
    ProductParentBaseView
)


class VariationChildrenFormPart(ProductChildrenBaseFormPart):
    invalid_modes = [ProductMode.VARIATION_CHILD, ProductMode.PACKAGE_PARENT, ProductMode.SUBSCRIPTION]
    priority = 0

    def get_form_defs(self):
        product = self.object
        if product.mode in self.invalid_modes:
            raise ValueError("Error! Invalid mode.")
        elif product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            form = VariableVariationChildrenForm
            template_name = "shuup/admin/products/variation/_variable_variation_children.jinja"
        else:
            form = formset_factory(SimpleVariationChildForm, SimpleVariationChildFormSet, extra=5, can_delete=True)
            template_name = "shuup/admin/products/variation/_simple_variation_children.jinja"

        form_defs = super(VariationChildrenFormPart, self).get_form_defs(form, template_name)
        for form_def in form_defs:
            yield form_def


class VariationVariablesFormPart(FormPart):
    form_def_name = "variables"
    priority = 1

    def get_form_defs(self):
        yield TemplatedFormDef(
            "variables",
            VariationVariablesDataForm,
            template_name="shuup/admin/products/variation/_variation_variables.jinja",
            required=False,
            kwargs={"parent_product": self.object, "request": self.request}
        )

    def form_valid(self, form):
        try:
            var_form = form["variables"]
        except KeyError:
            return
        var_form.save()


class ProductVariationViewToolbar(ProductParentBaseToolbar):
    def __init__(self, view):
        super(ProductVariationViewToolbar, self).__init__(view)

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


class ProductVariationView(ProductParentBaseView):
    template_name = "shuup/admin/products/variation/edit.jinja"
    form_part_classes = [VariationChildrenFormPart, VariationVariablesFormPart]
    toolbar_class = ProductVariationViewToolbar

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.variation_parent_id:
            # Redirect to the parent instead.
            return HttpResponseRedirect(
                reverse("shuup_admin:shop_product.edit_variation", kwargs={"pk": self.object.variation_parent_id})
            )
        return super(ProductVariationView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductVariationView, self).get_context_data(**kwargs)
        context["title"] = _("Edit Variation: %s") % self.object
        context["is_variation"] = self.object.is_variation_parent()
        return context

    def dispatch_command(self, request, command):
        product = self.object
        if command == "unvariate":
            product.clear_variation()
            messages.success(self.request, _("Variation cleared."))
        elif command == "simplify":
            product.simplify_variation()
            messages.success(self.request, _("Variation simplified."))
        else:
            raise Problem("Error! Unknown command: `%s`." % command)
        return HttpResponseRedirect(self.get_success_url())
