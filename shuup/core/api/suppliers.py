# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.fields import EnumField, FormattedDecimalField
from shuup.api.mixins import (
    PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin
)
from shuup.core.models import Product, Supplier
from shuup.core.suppliers.enums import StockAdjustmentType


class ProductStockStatusSerializer(serializers.Serializer):
    product = serializers.IntegerField(source="product_id")
    sku = serializers.CharField(source="product.sku")
    logical_count = FormattedDecimalField(coerce_to_string=False)
    physical_count = FormattedDecimalField(coerce_to_string=False)
    message = serializers.CharField()
    error = serializers.CharField()
    stock_managed = serializers.BooleanField()


class StockAdjustmentSerializer(serializers.Serializer):
    type = EnumField(StockAdjustmentType, default=StockAdjustmentType.INVENTORY)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all_except_deleted())
    delta = FormattedDecimalField()


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class SupplierProductsSerialzier(serializers.Serializer):
    products = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all_except_deleted()),
        required=False
    )
    skus = serializers.ListField(
        child=serializers.SlugRelatedField(queryset=Product.objects.all_except_deleted(), slug_field="sku"),
        required=False
    )


class SupplierViewSet(SearchableMixin, PermissionHelperMixin, ProtectedModelViewSetMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a supplier by its ID.

    list: Lists all available suppliers.

    delete: Deletes a supplier.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new supplier.

    update: Fully updates an existing supplier.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing supplier.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    search_fields = SearchableMixin.search_fields + ("name",)

    def get_view_name(self):
        return _("Suppliers")

    @classmethod
    def get_help_text(cls):
        return _("Suppliers can be listed, fetched, created, updated and deleted. Stocks can be updated.")

    def get_serializer_class(self):
        if self.action in ["update_stocks", "stock_statuses"]:
            return SupplierProductsSerialzier
        elif self.action == "adjust_stock":
            return StockAdjustmentSerializer
        return super(SupplierViewSet, self).get_serializer_class()

    @schema_serializer_class(StockAdjustmentSerializer)
    @detail_route(methods=['post'])
    def adjust_stock(self, request, pk=None):
        supplier = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            supplier.adjust_stock(
                product_id=serializer.validated_data["product"].id,
                delta=serializer.validated_data["delta"],
                type=serializer.validated_data["type"],
                created_by=request.user
            )
        except NotImplementedError:
            raise serializers.ValidationError("This supplier does not support stock adjustments")
        status = supplier.get_stock_status(serializer.validated_data["product"].id)
        return Response(ProductStockStatusSerializer(status).data)

    @schema_serializer_class(SupplierProductsSerialzier)
    @detail_route(methods=["post"])
    def update_stocks(self, request, pk=None):
        supplier = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_ids = [product.id for product in (
            serializer.validated_data.get("products") or
            serializer.validated_data.get("skus") or
            Product.objects.all_except_deleted().filter(shop_products__suppliers=supplier)
        )]
        try:
            supplier.update_stocks(product_ids)
        except NotImplementedError:
            raise serializers.ValidationError("This supplier does not support stock updates")
        return Response()

    @schema_serializer_class(SupplierProductsSerialzier)
    @detail_route(methods=["get"])
    def stock_statuses(self, request, pk=None):
        supplier = self.get_object()
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        product_ids = [product.id for product in (
            serializer.validated_data.get("products") or
            serializer.validated_data.get("skus") or
            Product.objects.all_except_deleted().filter(shop_products__suppliers=supplier)
        )]
        statuses = supplier.get_stock_statuses(product_ids)
        return Response(ProductStockStatusSerializer((statuses and statuses.values()), many=True).data)
