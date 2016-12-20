# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import django_filters
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import filters, serializers, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shuup.core.models import Product, ProductMedia, ShopProduct, Supplier
from shuup.utils.numbers import parse_decimal_string


class ShopProductSerializer(serializers.ModelSerializer):
    orderable = serializers.SerializerMethodField()

    class Meta:
        model = ShopProduct
        exclude = ("id", "product")
        extra_kwargs = {
            "visibility_groups": {"required": False},
            "shipping_methods": {"required": False},
            "suppliers": {"required": False},
            "payment_methods": {"required": False},
            "categories": {"required": False},
        }

    def get_orderable(self, shop_product):
        supplier = shop_product.suppliers.first()
        customer = self.context["request"].customer
        quantity = shop_product.minimum_purchase_quantity
        return shop_product.is_orderable(
            supplier=supplier, customer=customer, quantity=quantity
        )


class ProductMediaSerializer(serializers.ModelSerializer):
    translations = TranslatedFieldsField(shared_model=ProductMedia)
    url = serializers.SerializerMethodField()

    class Meta:
        fields = ("kind", "ordering", "public", "purchased", "shops", "url", "translations")
        model = ProductMedia

    def get_url(self, product_media):
        if product_media.external_url:
            return product_media.external_url
        return self.context["request"].build_absolute_uri(product_media.file.url)


class ProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)
    shop_products = ShopProductSerializer(many=True, read_only=True)
    primary_image = ProductMediaSerializer(read_only=True)
    media = ProductMediaSerializer(read_only=True, many=True)

    class Meta:
        fields = "__all__"
        model = Product


class ProductStockStatusSerializer(serializers.Serializer):
    stocks = serializers.SerializerMethodField()

    def get_stocks(self, product):
        stocks = []
        supplier_qs = Supplier.objects.filter(shop_products__product=product).distinct()

        # filtered by supplier
        supplier_id = int(parse_decimal_string(self.context["request"].query_params.get("supplier", 0)))
        if supplier_id:
            supplier_qs = supplier_qs.filter(pk=supplier_id)

        for supplier in supplier_qs:
            stock_status = supplier.get_stock_status(product.id)

            stocks.append({
                "id": supplier.id,
                "name": supplier.name,
                "type": supplier.type,
                "logical_count": stock_status.logical_count,
                "physical_count": stock_status.physical_count,
                "message": stock_status.message,
                "error": stock_status.error
            })

        return {
            "product": product.id,
            "sku": product.sku,
            "stocks": stocks
        }

    def to_representation(self, obj):
        # flatten data
        return super(ProductStockStatusSerializer, self).to_representation(obj).get("stocks")


class ProductFilter(FilterSet):
    product = django_filters.NumberFilter(name="pk", lookup_expr="exact")
    sku = django_filters.CharFilter(name="sku", lookup_expr="exact")
    supplier = django_filters.ModelChoiceFilter(name="shop_products__suppliers",
                                                queryset=Supplier.objects.all(),
                                                lookup_expr="exact")

    class Meta:
        model = Product
        fields = ["id", "product", "sku", "supplier"]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filter_class = ProductFilter

    def get_view_name(self):
        return _("Products")

    def get_view_description(self, html=False):
        return _("Products can be listed, fetched, created, updated and deleted.")

    def get_queryset(self):
        if getattr(self.request.user, 'is_superuser', False):
            return Product.objects.all_except_deleted()
        return Product.objects.listed(
            customer=self.request.customer,
            shop=self.request.shop
        )

    def perform_destroy(self, instance):
        instance.soft_delete(self.request.user)

    @list_route(methods=['get'])
    def stocks(self, request):
        product_qs = self.filter_queryset(self.get_queryset()).distinct()
        context = {'request': request}
        page = self.paginate_queryset(product_qs)
        serializer = ProductStockStatusSerializer((page or product_qs), many=True, context=context)
        return Response(serializer.data)


class ShopProductViewSet(viewsets.ModelViewSet):
    queryset = ShopProduct.objects.none()
    serializer_class = ShopProductSerializer

    def get_queryset(self):
        if getattr(self.request.user, 'is_superuser', False):
            products = Product.objects.all_except_deleted()
        else:
            products = Product.objects.listed(
                customer=self.request.customer,
                shop=self.request.shop
            )
        return ShopProduct.objects.filter(id__in=products)

    def get_view_name(self):
        return _("Shop Products")

    def get_view_description(self, html=False):
        return _("Shop Products can be listed, fetched, created, updated and deleted.")
