# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import django_filters
import six
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import filters, serializers, viewsets

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.models import (
    Product, ProductMode, ProductVariationLinkStatus, ProductVariationVariable,
    ProductVariationVariableValue
)
from shuup.core.models._product_variation import get_all_available_combinations


class ProductSimpleVariationSerializer(serializers.Serializer):
    products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True)


class ProductLinkVariationVariableSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)
    hash = serializers.CharField(max_length=40, min_length=40, required=True)
    status = EnumField(enum=ProductVariationLinkStatus, required=False)

    def validate(self, data):
        if self.context["request"].method in ("PUT", "POST") and not data.get("product"):
            raise serializers.ValidationError("`product` is required for this method.")
        return data


class ProductVariationVariableResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, product):
        combination_result = []

        if product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            for combination in get_all_available_combinations(product):
                combination_result.append({
                    "product": combination["result_product_pk"],
                    "sku_part": combination["sku_part"],
                    "hash": combination["hash"],
                    "combination": {
                        force_text(k): force_text(v) for k, v in six.iteritems(combination["variable_to_value"])
                    }
                })

        return {"combinations": combination_result}


class ProductVariationVariableValueSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=ProductVariationVariableValue, required=True)

    class Meta:
        exclude = ("identifier",)
        model = ProductVariationVariableValue


class ProductVariationVariableSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=ProductVariationVariable, required=True)
    values = ProductVariationVariableValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariationVariable
        exclude = ("identifier",)

    def create(self, validated_data):
        variable = super(ProductVariationVariableSerializer, self).create(validated_data)
        variable.product.verify_mode()
        variable.product.save()
        return variable

    def update(self, instance, validated_data):
        instance = super(ProductVariationVariableSerializer, self).update(instance, validated_data)
        instance.product.verify_mode()
        instance.product.save()
        return instance


class ProductVariationVariableFilter(FilterSet):
    product = django_filters.ModelChoiceFilter(name="product",
                                               queryset=Product.objects.all(),
                                               lookup_expr="exact")

    class Meta:
        model = ProductVariationVariable
        fields = ["product"]


class ProductVariationVariableValueFilter(FilterSet):
    product = django_filters.ModelChoiceFilter(name="variable__product",
                                               queryset=Product.objects.all(),
                                               lookup_expr="exact")
    variable = django_filters.ModelChoiceFilter(name="variable",
                                                queryset=ProductVariationVariable.objects.all(),
                                                lookup_expr="exact")

    class Meta:
        model = ProductVariationVariableValue
        fields = ["product", "variable"]


class ProductVariationVariableViewSet(PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a product variation variable by its ID.

    list: Lists all available product variation variables.

    delete: Deletes a product variation variable.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new product variation variable.

    update: Fully updates an existing product variation variable.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing product variation variable.
    You can update only a set of attributes.
    """

    queryset = ProductVariationVariable.objects.all()
    serializer_class = ProductVariationVariableSerializer
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filter_class = ProductVariationVariableFilter

    def perform_destroy(self, instance):
        product = instance.product
        super(ProductVariationVariableViewSet, self).perform_destroy(instance)
        product.verify_mode()
        product.save()

    def get_view_name(self):
        return _("Product Variation Variable")

    @classmethod
    def get_help_text(cls):
        return _("Product variation variables can be listed, fetched, created, updated and deleted.")


class ProductVariationVariableValueViewSet(PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a product variation variable value by its ID.

    list: Lists all available product variation variable values.

    delete: Deletes a product variation variable value.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new product variation variable value.

    update: Fully updates an existing product variation variable value.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing product variation variable value.
    You can update only a set of attributes.
    """

    queryset = ProductVariationVariableValue.objects.all()
    serializer_class = ProductVariationVariableValueSerializer
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filter_class = ProductVariationVariableValueFilter

    def get_view_name(self):
        return _("Product Variation Variable Value")

    @classmethod
    def get_help_text(cls):
        return _("Product variation variable values can be listed, fetched, created, updated and deleted.")
