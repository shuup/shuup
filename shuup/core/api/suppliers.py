# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES, FORMATTED_DECIMAL_FIELD_MAX_DIGITS
)
from shuup.core.models import Product, Supplier
from shuup.core.suppliers.enums import StockAdjustmentType
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


class StockAdjustmentSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=StockAdjustmentType.choices(), default=StockAdjustmentType.INVENTORY)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all_except_deleted())
    delta = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)

    def create(self, validated_data):
        supplier = validated_data["supplier"]
        product_id = validated_data["product"].pk
        delta = validated_data["delta"]
        type = validated_data["type"]
        try:
            return supplier.adjust_stock(product_id, delta, type=type)
        except NotImplementedError:
            raise serializers.ValidationError("This supplier does not support stock adjustments")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "type"]


class SupplierViewSet(PermissionHelperMixin, viewsets.ReadOnlyModelViewSet):
    """
    retrieve: Fetches a supplier by its ID.

    list: Lists all available suppliers.
    """

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get_view_name(self):
        return _("Suppliers")

    @classmethod
    def get_help_text(cls):
        return _("Suppliers can be listed and fetched and stock can be updated.")

    @schema_serializer_class(StockAdjustmentSerializer)
    @detail_route(methods=['get', 'post'])
    def stock(self, request, pk=None):
        """
        Retrieve or Update the current stocks of the Supplier.
        You can filter the stocks through `product` and `sku` parameters.
        """

        if request.method == 'POST':
            return self._adjust_stock(request, pk)

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

    def _adjust_stock(self, request, pk=None):
        supplier = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(supplier=supplier)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
