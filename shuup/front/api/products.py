# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from collections import defaultdict

import six
from django.utils.translation import ugettext_lazy as _
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import list_route
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.products import ProductSerializer
from shuup.core.models import (
    Category, Product, ProductCrossSellType, ShopProduct
)
from shuup.front.utils.product_statistics import get_best_selling_product_info
from shuup.utils.numbers import parse_decimal_string


class FrontProductSerializer(ProductSerializer):
    cross_sell = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = "__all__"

    def get_cross_sell(self, product):
        request = self.context["request"]

        cross_sell_data = {
            "recommended": [],
            "related": [],
            "computed": [],
            "bought_with": []
        }

        keys = {
            ProductCrossSellType.RECOMMENDED: "recommended",
            ProductCrossSellType.RELATED: "related",
            ProductCrossSellType.COMPUTED: "computed",
            ProductCrossSellType.BOUGHT_WITH: "bought_with",
        }

        for cross_sell in product.cross_sell_1.all():
            try:
                shop_product = cross_sell.product2.get_shop_instance(request.shop)
            except ShopProduct.DoesNotExist:
                continue

            supplier = shop_product.suppliers.first()
            quantity = shop_product.minimum_purchase_quantity

            if not shop_product.is_orderable(supplier=supplier, customer=request.customer, quantity=quantity):
                continue

            key = keys[cross_sell.type]
            cross_sell_data[key].append(cross_sell.product2.id)

        return cross_sell_data


class FrontProductFilter(FilterSet):
    category = filters.ModelChoiceFilter(name="shop_products__categories",
                                         queryset=Category.objects.all_except_deleted(),
                                         lookup_expr="exact")

    class Meta:
        model = Product
        fields = ["category"]


class FrontProductViewSet(PermissionHelperMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list: Lists all available products to be present in storefront.
    """

    queryset = Product.objects.none()
    serializer_class = FrontProductSerializer
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    filter_class = FrontProductFilter

    def get_view_name(self):
        return _("Storefront Products")

    @classmethod
    def get_help_text(cls):
        return _("Storefront products can be listed and fetched.")

    def get_queryset(self):
        return Product.objects.listed(
            customer=self.request.customer,
            shop=self.request.shop
        ).filter(
            shop_products__shop=self.request.shop,
            variation_parent__isnull=True
        )

    @list_route(methods=['get'])
    def newest(self, request):
        """
        Returns the top 20 (default) new products.
        To change the number of products, set the `limit` query param.
        """
        limit = int(parse_decimal_string(request.query_params.get("limit", 20)))
        product_qs = self.filter_queryset(self.get_queryset()).order_by("-id").distinct()
        serializer = ProductSerializer(product_qs[:limit], many=True, context={"request": request})
        return Response(serializer.data)

    @list_route(methods=['get'])
    def best_selling(self, request):
        """
        Returns the top 20 (default) best selling products.
        To change the number of products, set the `limit` query param.
        """
        limit = int(parse_decimal_string(request.query_params.get("limit", 20)))
        best_selling_products = get_best_selling_product_info(shop_ids=[request.shop.pk])
        combined_variation_products = defaultdict(int)

        for product_id, parent_id, qty in best_selling_products:
            if parent_id:
                combined_variation_products[parent_id] += qty
            else:
                combined_variation_products[product_id] += qty

        # take here the top `limit` records, because the filter_queryset below can mess with our work
        product_ids = [
            d[0] for d in sorted(six.iteritems(combined_variation_products), key=lambda i: i[1], reverse=True)[:limit]
        ]

        products_qs = Product.objects.filter(id__in=product_ids)
        products_qs = self.filter_queryset(products_qs).distinct()
        serializer = ProductSerializer(products_qs, many=True, context={"request": request})
        return Response(serializer.data)
