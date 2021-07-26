# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from typing import Iterable, Tuple

from shuup.admin.utils.permissions import has_permission
from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.core.models import Product, ProductMode, ShopProduct, ShopProductVisibility


class ProductAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 11

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.product"

    def has_permission(self, user):
        return has_permission(user, "product.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        search_mode = kwargs.get("search_mode")
        shop = kwargs.get("shop")
        supplier = kwargs.get("supplier")
        sales_units = kwargs.get("sales_units")

        qs = Product.objects.all_except_deleted(shop=shop)
        qs = qs.exclude(Q(shop_products__visibility=ShopProductVisibility.NOT_VISIBLE)).filter(
            Q(translations__name__icontains=search_term)
            | Q(sku__icontains=search_term)
            | Q(barcode__icontains=search_term)
        )
        if supplier:
            qs = qs.filter(shop_products__suppliers=supplier)
        if sales_units:
            qs = qs.filter(sales_unit__translations__symbol__in=sales_units.strip().split(","))
        if search_mode == "main":
            qs = qs.filter(
                mode__in=[
                    ProductMode.SIMPLE_VARIATION_PARENT,
                    ProductMode.VARIABLE_VARIATION_PARENT,
                    ProductMode.NORMAL,
                ]
            )
        elif search_mode == "parent_product":
            qs = qs.filter(mode__in=[ProductMode.SIMPLE_VARIATION_PARENT, ProductMode.VARIABLE_VARIATION_PARENT])
        elif search_mode == "sellable_mode_only":
            qs = qs.exclude(Q(mode__in=[ProductMode.SIMPLE_VARIATION_PARENT, ProductMode.VARIABLE_VARIATION_PARENT]))
        qs = qs.distinct()

        return [{"id": instance.id, "name": instance.name} for instance in qs]


class ShopProductAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 12

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.shopproduct"

    def has_permission(self, user):
        return has_permission(user, "shop_product.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        shop = kwargs.get("shop")
        supplier = kwargs.get("supplier")

        if shop:
            qs = ShopProduct.objects.filter(shop=shop)
        else:
            qs = ShopProduct.objects.all()
        if supplier:
            qs = qs.filter(suppliers=supplier)
        qs = qs.filter(product__deleted=False, product__translations__name__icontains=search_term)
        return [{"id": instance.id, "name": instance.product.name} for instance in qs]
