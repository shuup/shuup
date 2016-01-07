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
from django.forms.formsets import BaseFormSet, DELETION_FIELD_NAME
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.widgets import ProductChoiceWidget
from shoop.core.excs import ImpossibleProductModeException, Problem
from shoop.core.models import Product


class SimpleVariationChildForm(forms.Form):
    # TODO: Add a mode for ProductChoiceWidget to only allow eligible variation children to be selected
    child = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=ProductChoiceWidget(),
        label=_('child')
    )


class SimpleVariationChildFormSet(BaseFormSet):
    def __init__(self, **kwargs):
        kwargs.pop("empty_permitted", None)
        self.request = kwargs.pop("request", None)
        self.parent_product = kwargs.pop("parent_product")
        kwargs["initial"] = [
            {"child": product}
            for product
            in self.parent_product.variation_children.all_except_deleted()
            ]
        super(SimpleVariationChildFormSet, self).__init__(**kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(SimpleVariationChildFormSet, self)._construct_form(i, **kwargs)
        form.fields[DELETION_FIELD_NAME].label = _("Unlink")
        return form

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
                    six.raise_from(Problem(_("Unable to link %s: %s") % (child_product, ipme)), ipme)

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
