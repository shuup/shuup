# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.http import HttpResponseRedirect
from django.views.generic import UpdateView

from shuup.admin.base import MenuEntry
from shuup.admin.form_part import (
    FormPart, FormPartsViewMixin, TemplatedFormDef
)
from shuup.admin.toolbar import get_default_edit_toolbar, Toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import Product
from shuup.utils.django_compat import reverse


class ProductChildrenBaseFormPart(FormPart):
    invalid_modes = []
    priority = 0
    form_name = None

    def get_form_defs(self, form, template_name):
        yield TemplatedFormDef(
            "children",
            form,
            template_name=template_name,
            required=False,
            kwargs={"parent_product": self.object, "request": self.request}
        )

    def form_valid(self, form):
        try:
            children_formset = form["children"]
        except KeyError:
            return
        children_formset.save()


class ProductParentBaseToolbar(Toolbar):
    def __init__(self, view):
        super(ProductParentBaseToolbar, self).__init__()
        self.view = view
        self.parent_product = view.object
        self.request = view.request
        get_default_edit_toolbar(self.view, "product_form", with_split_save=False, toolbar=self)


class ProductParentBaseView(FormPartsViewMixin, UpdateView):
    model = Product
    context_object_name = "product"
    form_class = forms.Form
    form_part_classes = []
    toolbar_class = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        parent = self.object.get_all_package_parents().first()
        if parent:
            # By default, redirect to the first parent
            return HttpResponseRedirect(
                reverse("shuup_admin:shop_product.edit_package", kwargs={"pk": parent.id})
            )
        return super(ProductParentBaseView, self).dispatch(request, *args, **kwargs)

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=self.object,
                url=get_model_url(self.object, shop=self.request.shop)
            )
        ]

    def post(self, request, *args, **kwargs):
        command = request.POST.get("command")
        if command:
            return self.dispatch_command(request, command)
        return super(ProductParentBaseView, self).post(request, *args, **kwargs)

    def get_form_part_classes(self):
        for form_part_class in self.form_part_classes:
            yield form_part_class

    def get_context_data(self, **kwargs):
        context = super(ProductParentBaseView, self).get_context_data(**kwargs)
        if self.toolbar_class:
            context["toolbar"] = self.toolbar_class(self)
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
        pass
