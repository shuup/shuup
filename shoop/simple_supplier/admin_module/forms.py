# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.core.models import Product, StockBehavior, Supplier
from shoop.simple_supplier.utils import (
    get_stock_adjustment_div, get_stock_information_html
)


class SimpleSupplierForm(forms.Form):
    def __init__(self, **kwargs):
        self.product = kwargs.pop("product")
        self.request = kwargs.pop("request")
        super(SimpleSupplierForm, self).__init__(**kwargs)
        self.products = []
        if self.product:
            self._build_fields()

    def _build_fields(self):
        if self.product.is_variation_parent():
            self.products = Product.objects.filter(
                variation_parent=self.product, stock_behavior=StockBehavior.STOCKED)
        else:
            if self.product.stock_behavior == StockBehavior.STOCKED:
                self.products = [self.product]

    def save(self):
        return  # No need to save anything since all stock adjustments are made by AJAX.

    def get_suppliers(self, product):
        return Supplier.objects.filter(shop_products__product=product, module_identifier="simple_supplier")

    def get_stock_information(self, supplier, product):
        return get_stock_information_html(supplier, product)

    def get_stock_adjustment_form(self, supplier, product):
        return get_stock_adjustment_div(self.request, supplier, product)


class SimpleSupplierFormPart(FormPart):
    priority = 15
    name = "simple_supplier"
    form = SimpleSupplierForm

    def get_form_defs(self):
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shoop/simple_supplier/admin/product_form_part.jinja",
            required=False,
            kwargs={"product": self.object, "request": self.request}
        )

    def form_valid(self, form):
        return  # No need to save anything since all stock adjustments are made by AJAX
