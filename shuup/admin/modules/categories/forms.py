# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms import ShuupAdminForm
from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.forms.widgets import QuickAddCategorySelect, TextEditorWidget
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.forms import filter_form_field_choices
from shuup.core.models import (
    Category, CategoryStatus, Product, ShopProduct, ShopProductVisibility
)
from shuup.utils.django_compat import force_text


class CategoryBaseForm(ShuupAdminForm):
    class Meta:
        model = Category
        fields = (
            "parent",
            "status",
            "ordering",
            "visibility",
            "visible_in_menu",
            "visibility_groups",
            "name",
            "image",
            "description",
            "slug",
        )

        widgets = {
            "status": forms.RadioSelect,
            "visibility": forms.RadioSelect,
            "description": TextEditorWidget(),
            "parent": QuickAddCategorySelect(editable_model="shuup.Category")
        }

    def __init__(self, request, **kwargs):
        self.request = request
        super(CategoryBaseForm, self).__init__(**kwargs)
        # Exclude `DELETED`. We don't want people to use that field to set a category as deleted.
        filter_form_field_choices(self.fields["status"], (CategoryStatus.DELETED.value,), invert=True)

        # Exclude current category from parents, because it cannot be its own child anyways
        category_queryset = Category.objects.filter(shops=get_shop(request)).exclude(status=CategoryStatus.DELETED)
        self.fields["parent"].queryset = category_queryset
        self.fields["parent"].choices = [(None, "----")] + [
            (category.pk, force_text(category)) for category in category_queryset.exclude(id=kwargs["instance"].pk)
        ]

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        if parent and self.request.shop not in parent.shops.all():
            raise ValidationError(_("Can't use this category as a parent for this shop."), code="invalid_parent")
        return parent

    def save(self, commit=True):
        instance = super(CategoryBaseForm, self).save(commit)
        instance.shops.add(self.request.shop)


class CategoryProductForm(forms.Form):
    primary_products = Select2MultipleField(
        label=_("Primary Category"),
        help_text=_("Set this category as a primary category for selected products."),
        model=Product,
        required=False)
    additional_products = Select2MultipleField(
        label=_("Additional Category"),
        help_text=_("Add selected products to this category."),
        model=Product,
        required=False)
    remove_products = forms.MultipleChoiceField(
        label=_("Remove Products"),
        help_text=_("Remove selected products from this category."),
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
            shop_product.visibility_groups.set(visibility_groups)
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
