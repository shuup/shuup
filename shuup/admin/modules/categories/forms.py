# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms import ShuupAdminForm
from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.forms.widgets import TextEditorWidget
from shuup.admin.utils.forms import filter_form_field_choices
from shuup.core.models import (
    Category, CategoryStatus, Product, Shop, ShopProduct,
    ShopProductVisibility
)


class CategoryBaseForm(ShuupAdminForm):
    class Meta:
        model = Category
        fields = (
            "parent",
            "shops",
            "status",
            "ordering",
            "visibility",
            "visibility_groups",
            "name",
            "image",
            "description",
            "slug",
        )

        widgets = {
            "status": forms.RadioSelect,
            "visibility": forms.RadioSelect,
            "description": TextEditorWidget()
        }

    def __init__(self, **kwargs):
        if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            initial = kwargs.get("initial", {})
            initial["shops"] = [Shop.objects.first().pk]
            kwargs["initial"] = initial

        super(CategoryBaseForm, self).__init__(**kwargs)
        # Exclude `DELETED`. We don't want people to use that field to set a category as deleted.
        filter_form_field_choices(self.fields["status"], (CategoryStatus.DELETED.value,), invert=True)

        # Exclude current category from parents, because it cannot be its own child anyways
        filter_form_field_choices(self.fields["parent"], (kwargs["instance"].pk,), invert=True)

        if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            self.fields["shops"].disabled = True

    def clean_shops(self):
        shops = self.cleaned_data["shops"]
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            return shops
        return [Shop.objects.first().pk]


class CategoryProductForm(forms.Form):
    primary_products = Select2MultipleField(
        label=_("Primary Category"),
        help_text=_("Set this category as a primary for selected products."),
        model=Product,
        required=False)
    additional_products = Select2MultipleField(
        label=_("Additional Category"),
        help_text=_("Add selected products to this category"),
        model=Product,
        required=False)
    remove_products = forms.MultipleChoiceField(
        label=_("Remove Products"),
        help_text=_("Remove selected products from this category"),
        required=False)

    def __init__(self, shop, category, **kwargs):
        self.shop = shop
        self.category = category
        super(CategoryProductForm, self).__init__(**kwargs)
        self.fields["remove_products"].choices = [(None, "-----")] + [
            (obj.product.pk, obj.product.name) for obj in category.shop_products.filter(shop=shop)
        ]

    @atomic
    def save(self):
        data = self.cleaned_data
        is_visible = self.category.status == CategoryStatus.VISIBLE
        visibility_groups = self.category.visibility_groups.all()
        primary_product_ids = [int(product_id) for product_id in data.get("primary_products", [])]
        for shop_product in ShopProduct.objects.filter(
                Q(shop_id=self.shop.id),
                Q(product_id__in=primary_product_ids) | Q(product__variation_parent_id__in=primary_product_ids)):
            shop_product.primary_category = self.category
            shop_product.visibility = (
                ShopProductVisibility.ALWAYS_VISIBLE if is_visible else ShopProductVisibility.NOT_VISIBLE
            )
            shop_product.visibility_limit = self.category.visibility.value
            shop_product.visibility_groups = visibility_groups
            shop_product.save()
            shop_product.categories.add(self.category)

        additional_product_ids = [int(product_id) for product_id in data.get("additional_products", [])]
        for shop_product in ShopProduct.objects.filter(
                Q(shop_id=self.shop.id),
                Q(product_id__in=additional_product_ids) | Q(product__variation_parent_id__in=additional_product_ids)):
            shop_product.categories.add(self.category)

        remove_product_ids = [int(product_id) for product_id in data.get("remove_products", [])]
        for shop_product in ShopProduct.objects.filter(
                Q(product_id__in=remove_product_ids) | Q(product__variation_parent_id__in=remove_product_ids)):
            if shop_product.primary_category == self.category:
                if self.category in shop_product.categories.all():
                    shop_product.categories.remove(self.category)
                shop_product.primary_category = None
                shop_product.save()
            shop_product.categories.remove(self.category)
