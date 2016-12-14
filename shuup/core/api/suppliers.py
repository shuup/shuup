# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from rest_framework import serializers, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from shuup.core.models import Product, Supplier
from shuup.utils.numbers import parse_decimal_string


class ProductStockSerializer(serializers.Serializer):
    stock = serializers.SerializerMethodField()

    def get_stock(self, product):
        stock_status = self.context["supplier"].get_stock_status(product.id)

        return {
            "product": product.id,
            "sku": product.sku,
            "logical_count": stock_status.logical_count,
            "physical_count": stock_status.physical_count,
            "message": stock_status.message,
            "error": stock_status.error
        }

    def to_representation(self, obj):
        # just flatten data
        representation = super(ProductStockSerializer, self).to_representation(obj)
        return representation.get("stock")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "type"]


class SupplierViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for shuup.core.models.Supplier
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    @detail_route(methods=['get'])
    def stock(self, request, pk=None):
        supplier = self.get_object()

        if getattr(self.request.user, 'is_superuser', False):
            products_qs = Product.objects.all_except_deleted()
        else:
            products_qs = Product.objects.listed(
                customer=self.request.customer,
                shop=self.request.shop
            )

        products_qs = products_qs.filter(shop_products__suppliers=supplier)

        # filter by id
        product_id = int(parse_decimal_string(request.query_params.get("product", 0)))
        if product_id:
            products_qs = products_qs.filter(pk=product_id)

        # filter by sku
        product_sku = request.query_params.get("sku")
        if product_sku:
            products_qs = products_qs.filter(sku=product_sku)

        page = self.paginate_queryset(products_qs)
        context = {'request': request, 'supplier': supplier}
        serializer = ProductStockSerializer((page or products_qs), many=True, context=context)
        return Response(serializer.data)
