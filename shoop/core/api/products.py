# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
# TODO: Fix these imports once parler_rest>=1.2 is released
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from shoop.api._vendor.parler_rest.fields import TranslatedFieldsField
from shoop.api._vendor.parler_rest.serializers import \
    TranslatableModelSerializer
from shoop.core.models import Product, ShopProduct


class ShopProductSerializer(ModelSerializer):
    class Meta:
        model = ShopProduct
        extra_kwargs = {
            "visibility_groups": {"required": False},
            "shipping_methods": {"required": False},
            "suppliers": {"required": False},
            "payment_methods": {"required": False},
            "categories": {"required": False},
        }


class ProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)
    shop_products = ShopProductSerializer(many=True, read_only=True)

    class Meta:
        model = Product


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Product.objects.all_except_deleted()
        return Product.objects.list_visible(
            customer=self.request.customer,
            shop=self.request.shop
        )


class ShopProductViewSet(ModelViewSet):
    queryset = ShopProduct.objects.none()
    serializer_class = ShopProductSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            products = Product.objects.all_except_deleted()
        else:
            products = Product.objects.list_visible(
                customer=self.request.customer,
                shop=self.request.shop
            )
        return ShopProduct.objects.filter(id__in=products)
