# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.contrib import messages
from django.forms.formsets import DEFAULT_MIN_NUM, DEFAULT_MAX_NUM
from django.forms.models import BaseModelFormSet, ModelForm
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView
from shoop.admin.base import MenuEntry
from shoop.admin.forms.widgets import ProductChoiceWidget
from shoop.admin.toolbar import Toolbar, PostActionButton
from shoop.admin.utils.urls import get_model_url
from shoop.core.models import Product, ProductMedia, ProductCrossSell, ProductCrossSellType


class ProductCrossSellForm(ModelForm):
    class Meta:
        model = ProductCrossSell
        fields = (
            "product2",
            "weight",
            "type",
        )

    def __init__(self, **kwargs):
        self.product = kwargs.pop("product")
        super(ProductCrossSellForm, self).__init__(**kwargs)
        self.fields["product2"].widget = ProductChoiceWidget()
        self.fields["product2"].label = _("Product")

    def save(self, commit=True):
        self.instance.product1 = self.product
        return super(ProductCrossSellForm, self).save(commit=commit)


class ProductCrossSellFormSet(BaseModelFormSet):
    validate_min = False
    min_num = DEFAULT_MIN_NUM
    validate_max = False
    max_num = DEFAULT_MAX_NUM
    absolute_max = DEFAULT_MAX_NUM
    model = ProductMedia
    can_delete = True
    can_order = False
    extra = 5

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop("product")
        super(ProductCrossSellFormSet, self).__init__(*args, **kwargs)

    def form(self, **kwargs):
        kwargs.setdefault("product", self.product)
        return ProductCrossSellForm(**kwargs)


class ProductCrossSellEditView(UpdateView):
    model = Product
    template_name = "shoop/admin/products/edit_cross_sell.jinja"
    context_object_name = "product"
    form_class = ProductCrossSellFormSet

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text="%s" % self.object,
                url=get_model_url(self.object)
            )
        ]

    def get_context_data(self, **kwargs):
        context = super(ProductCrossSellEditView, self).get_context_data(**kwargs)
        context["title"] = _("Edit Cross-Sell: %s") % self.object
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-save",
                form_id="xsell_form",
                text=_("Save"),
                extra_css_class="btn-success",
            ),
        ])
        return context

    def get_form_kwargs(self):
        kwargs = super(ProductCrossSellEditView, self).get_form_kwargs()
        instance = kwargs.pop("instance", None)
        kwargs["queryset"] = ProductCrossSell.objects. \
            filter(product1=instance). \
            exclude(type=ProductCrossSellType.COMPUTED). \
            order_by("weight")
        kwargs["product"] = instance
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Changes saved."))
        return HttpResponseRedirect(self.request.path)
