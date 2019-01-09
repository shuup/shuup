# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.contrib import messages
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.widgets import ProductChoiceWidget
from shuup.core.excs import ImpossibleProductModeException, Problem
from shuup.core.models import Product

from .parent_forms import ProductChildBaseFormSet


class SimpleVariationChildForm(forms.Form):
    # TODO: Add a mode for ProductChoiceWidget to only allow eligible variation children to be selected
    child = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=ProductChoiceWidget(),
        label=_('child')
    )


class SimpleVariationChildFormSet(ProductChildBaseFormSet):
    deletion_label = _("Unlink")

    def __init__(self, **kwargs):
        self.parent_product = kwargs.pop("parent_product")
        kwargs["initial"] = [
            {"child": product}
            for product
            in self.parent_product.variation_children.all_except_deleted()
            ]
        super(SimpleVariationChildFormSet, self).__init__(**kwargs)

    def save(self):
        parent_product = self.parent_product
        current_products = set(parent_product.variation_children.all())
        selected_products, unlinked_products = self.get_selected_and_unlinked()

        with atomic():
            products_to_add = selected_products - current_products
            products_to_remove = current_products & unlinked_products
            for child_product in products_to_remove:
                child_product.unlink_from_parent()
            for child_product in products_to_add:
                try:
                    child_product.link_to_parent(parent_product)
                except ImpossibleProductModeException as ipme:
                    six.raise_from(
                        Problem(
                            _("Unable to link %(product)s: %(error)s") %
                            {"product": child_product, "error": ipme}
                        ), ipme
                    )

        message_parts = []
        if products_to_add:
            message_parts.append(_("New: %d") % len(products_to_add))
        if products_to_remove:
            message_parts.append(_("Removed: %d") % len(products_to_remove))
        if message_parts and self.request:
            messages.success(self.request, ", ".join(message_parts))

    def get_selected_and_unlinked(self):
        deleted_forms = self.deleted_forms
        unlinked_products = set()
        selected_products = set()
        for child_form in self.forms:
            child_product = child_form.cleaned_data.get("child")
            if not child_product:
                continue
            if child_form in deleted_forms:
                unlinked_products.add(child_product)
            else:
                selected_products.add(child_product)
        return (selected_products, unlinked_products)
