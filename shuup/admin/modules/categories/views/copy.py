# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic
from django.http.response import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from shuup.core.models import (
    Category, CategoryStatus, ShopProduct, ShopProductVisibility
)


class CategoryCopyVisibilityView(View):
    """
    Copy category visibility settings to all products with this category as the primary category.
    """
    @atomic
    def post(self, request, *args, **kwargs):
        try:
            category = Category.objects.prefetch_related("visibility_groups", "shops").get(pk=self.kwargs.get("pk"))
        except Category.DoesNotExist:
            return JsonResponse({"message": _("Invalid category")}, status=400)

        count = 0
        is_visible = category.status == CategoryStatus.VISIBLE
        category_shops = category.shops.all()
        category_visibility_groups = category.visibility_groups.all()
        for product in ShopProduct.objects.filter(shop__in=category_shops, primary_category__pk=category.pk):
            product.visibility = (
                ShopProductVisibility.ALWAYS_VISIBLE if is_visible else ShopProductVisibility.NOT_VISIBLE
            )
            product.visibility_limit = category.visibility.value
            product.visibility_groups.set(category_visibility_groups)
            product.save()
            count += 1
        return JsonResponse({"message": _("Visibility settings copied to %d product(s)") % count})
