# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.contrib import messages
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.widgets import ProductChoiceWidget
from shoop.admin.modules.products.utils import clear_existing_package
from shoop.core.excs import ImpossibleProductModeException, Problem
from shoop.core.models import Product

from .parent_forms import ProductChildBaseFormSet


class PackageChildForm(forms.Form):
    child = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=ProductChoiceWidget(),
        label="",
        required=True,
    )
    quantity = forms.DecimalField(
        min_value=0,
        label="",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=True,
    )


class PackageChildFormSet(ProductChildBaseFormSet):
    deletion_label = _("Remove")

    def __init__(self, **kwargs):
        self.parent_product = kwargs.pop("parent_product")
        kwargs["initial"] = [
            {
                "child": product,
                "quantity": quantity,
            }
            for (product, quantity)
            in six.iteritems(self.parent_product.get_package_child_to_quantity_map())
            ]
        super(PackageChildFormSet, self).__init__(**kwargs)

    def save(self):
        parent_product = self.parent_product
        current_products = set(parent_product.get_package_child_to_quantity_map())
        selected_products, removed_products, selected_quantities = self.get_selected_and_removed()

        with atomic():
            try:
                clear_existing_package(parent_product)
                parent_product.make_package(package_def=selected_quantities)
            except ImpossibleProductModeException as ipme:
                six.raise_from(
                    Problem(
                        _("Unable to make package %(product)s: %(error)s") %
                        {"product": parent_product, "error": ipme}
                    ), ipme
                )

        products_to_add = selected_products - current_products
        products_to_remove = current_products & removed_products

        message_parts = []
        if products_to_add:
            message_parts.append(_("New: %d") % len(products_to_add))
        if products_to_remove:
            message_parts.append(_("Removed: %d") % len(products_to_remove))
        if message_parts and self.request:
            messages.success(self.request, ", ".join(message_parts))

    def get_selected_and_removed(self):
        deleted_forms = self.deleted_forms
        removed_products = set()
        selected_products = set()
        selected_product_quantities = {}
        for child_form in self.forms:
            child_product = child_form.cleaned_data.get("child")
            if not child_product:
                continue
            if child_form in deleted_forms:
                removed_products.add(child_product)
            elif child_product != self.parent_product:
                selected_products.add(child_product)
            elif self.request and child_product == self.parent_product:
                messages.error(self.request, _("Couldn't add product %s to own package") % str(child_product))
            quantity = child_form.cleaned_data.get("quantity")
            selected_product_quantities[child_product] = quantity
        selected_quantities = {
            product: quantity
            for product, quantity
            in selected_product_quantities.items()
            if (product not in removed_products and product != self.parent_product)
        }

        return (selected_products, removed_products, selected_quantities)
