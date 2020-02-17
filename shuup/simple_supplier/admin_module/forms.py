# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.models import Product, Supplier
from shuup.simple_supplier.module import SimpleSupplierModule
from shuup.simple_supplier.utils import (
    get_stock_adjustment_div, get_stock_information_html
)


class SimpleSupplierForm(forms.Form):
    def __init__(self, **kwargs):
        self.product = kwargs.pop("product")
        self.request = kwargs.pop("request")
        super(SimpleSupplierForm, self).__init__(**kwargs)
        self.products = []
        self.module_name = SimpleSupplierModule.name
        self.supplier_model = Supplier
        if self.product:
            self._build_fields()

    def _build_fields(self):
        if self.product.is_variation_parent():
            self.products = Product.objects.filter(variation_parent=self.product)
        else:
            self.products = [self.product]

    def save(self):
        return  # No need to save anything since all stock adjustments are made by AJAX.

    def get_suppliers(self, product):
        return Supplier.objects.filter(shop_products__product=product, module_identifier="simple_supplier").distinct()

    def can_manage_stock(self):
        return Supplier.objects.filter(module_identifier="simple_supplier", stock_managed=True).exists()

    def get_stock_information(self, supplier, product):
        return get_stock_information_html(supplier, product)

    def get_stock_adjustment_form(self, supplier, product):
        return get_stock_adjustment_div(self.request, supplier, product)


class SimpleSupplierFormPart(FormPart):
    priority = 15
    name = "simple_supplier"
    form = SimpleSupplierForm

    def get_form_defs(self):
        if self.object.pk:  # Don't yield form if product is in new mode
            yield TemplatedFormDef(
                name=self.name,
                form_class=self.form,
                template_name="shuup/simple_supplier/admin/product_form_part.jinja",
                required=False,
                kwargs={"product": self.object.product, "request": self.request}
            )

    def form_valid(self, form):
        return  # No need to save anything since all stock adjustments are made by AJAX
