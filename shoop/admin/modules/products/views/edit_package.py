# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from shoop.admin.modules.products.forms import (
    PackageChildForm, PackageChildFormSet
)
from shoop.admin.modules.products.utils import clear_existing_package
from shoop.admin.toolbar import PostActionButton
from shoop.core.models import ProductMode
from shoop.utils.excs import Problem

from .edit_parent import (
    ProductChildrenBaseFormPart, ProductParentBaseToolbar,
    ProductParentBaseView
)


class ProductChildrenFormPart(ProductChildrenBaseFormPart):
    invalid_modes = [
        ProductMode.VARIATION_CHILD, ProductMode.VARIABLE_VARIATION_PARENT,
        ProductMode.SIMPLE_VARIATION_PARENT
    ]
    priority = 0

    def get_form_defs(self):
        product = self.object
        if product.mode in self.invalid_modes:
            raise ValueError("Invalid mode")
        else:
            form = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
            template_name = "shoop/admin/products/package/_package_children.jinja"

        form_defs = super(ProductChildrenFormPart, self).get_form_defs(form, template_name)
        for form_def in form_defs:
            yield form_def


class ProductPackageViewToolbar(ProductParentBaseToolbar):
    def __init__(self, view):
        super(ProductPackageViewToolbar, self).__init__(view)

        if self.parent_product.get_package_child_to_quantity_map():
            self.append(PostActionButton(
                post_url=self.request.path,
                name="command",
                value="clear_package",
                confirm=_("Are you sure? This will remove all products from package."),
                text=_("Clear package"),
                extra_css_class="btn-danger",
                icon="fa fa-times"
            ))


class ProductPackageView(ProductParentBaseView):
    template_name = "shoop/admin/products/package/edit.jinja"
    form_part_classes = [ProductChildrenFormPart]
    toolbar_class = ProductPackageViewToolbar

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        parent = self.object.get_all_package_parents().first()
        if parent:
            # By default, redirect to the first parent
            return HttpResponseRedirect(
                reverse("shoop_admin:product.edit_package", kwargs={"pk": parent.id})
            )
        return super(ProductPackageView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductPackageView, self).get_context_data(**kwargs)
        context["title"] = _("Edit Package: %s") % self.object
        context["is_package"] = self.object.is_package_parent()
        return context

    def dispatch_command(self, request, command):
        product = self.object
        if command == "clear_package":
            clear_existing_package(product)
            messages.success(self.request, _("Package cleared."))
        else:
            raise Problem("Unknown command: %s" % command)
        return HttpResponseRedirect(self.get_success_url())
