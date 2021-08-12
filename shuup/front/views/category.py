# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.views.generic import DetailView, TemplateView

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import Category, ShopProductVisibility, Supplier
from shuup.front.utils.sorts_and_filters import ProductListForm, get_product_queryset, get_query_filters, sort_products


def get_context_data(context, request, category, product_filters):
    data = request.GET
    context["form"] = form = ProductListForm(request=request, shop=request.shop, category=category, data=data)
    form.full_clean()
    data = form.cleaned_data
    if "sort" in form.fields and not data.get("sort"):
        # Use first choice by default
        data["sort"] = form.fields["sort"].widget.choices[0][0]

    catalog = ProductCatalog(
        ProductCatalogContext(
            shop=request.shop,
            user=getattr(request, "user", None),
            contact=getattr(request, "customer", None),
            purchasable_only=True,
            supplier=data.get("supplier") or None,
            visibility=ShopProductVisibility.LISTED,
        )
    )
    products = (
        catalog.get_products_queryset()
        .filter(**product_filters)
        .filter(get_query_filters(request, category, data=data))
        .select_related("primary_image", "sales_unit", "tax_class")
        .prefetch_related("translations", "sales_unit__translations")
    )
    products = get_product_queryset(products, request, category, data)
    products = sort_products(request, category, products, data).distinct()
    context["page_size"] = data.get("limit", 12)
    context["products"] = products

    if "supplier" in data:
        context["supplier"] = data.get("supplier")

    return context


class CategoryView(DetailView):
    template_name = "shuup/front/product/category.jinja"
    model = Category
    template_object_name = "category"

    def get_queryset(self):
        return self.model.objects.all_visible(
            customer=self.request.customer,
            shop=self.request.shop,
        )

    def get_product_filters(self):
        return {
            "shop_products__shop": self.request.shop,
            "variation_parent__isnull": True,
            "shop_products__categories__in": self.object.get_descendants(include_self=True),
            "shop_products__suppliers__in": Supplier.objects.enabled(shop=self.request.shop),
        }

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        return get_context_data(context, self.request, self.object, self.get_product_filters())


class AllCategoriesView(TemplateView):
    template_name = "shuup/front/product/category.jinja"

    def get_product_filters(self):
        category_ids = Category.objects.all_visible(
            customer=self.request.customer,
            shop=self.request.shop,
        ).values_list("id", flat=True)
        return {
            "shop_products__shop": self.request.shop,
            "variation_parent__isnull": True,
            "shop_products__categories__id__in": category_ids,
            "shop_products__suppliers__in": Supplier.objects.enabled(shop=self.request.shop),
        }

    def get_context_data(self, **kwargs):
        context = super(AllCategoriesView, self).get_context_data(**kwargs)
        context["category"] = None
        return get_context_data(context, self.request, None, self.get_product_filters())
