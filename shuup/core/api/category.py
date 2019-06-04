# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import django_filters
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers, viewsets

from shuup.api.fields import Base64FileField, EnumField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import (
    Category, CategoryStatus, CategoryVisibility, Shop
)
from shuup.utils.filer import filer_image_from_upload


class CategorySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Category)
    status = EnumField(CategoryStatus)
    visibility = EnumField(CategoryVisibility)
    image = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(CategorySerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request.method == "POST":
            self.fields["image"] = Base64FileField(required=False, write_only=True)
            self.fields["image_path"] = serializers.CharField(required=False, write_only=True)
        elif request.method == "GET":
            self.fields["image"] = serializers.SerializerMethodField()

    def create(self, validated_data):
        if "image_path" in validated_data:
            validated_data.pop("image_path")
        return super(CategorySerializer, self).create(validated_data)

    def validate(self, data):
        if data.get("image") and data.get("image_path"):
            data["image"] = filer_image_from_upload(
                self.context["request"], path=data["image_path"], upload_data=data["image"])
        elif data.get("image"):
            raise serializers.ValidationError("Path is required when sending a Category image.")
        return data

    def get_image(self, category):
        if category.image:
            return self.context["request"].build_absolute_uri(category.image.url)

    class Meta:
        model = Category
        fields = '__all__'


class CategoryFilter(FilterSet):
    parent = django_filters.ModelChoiceFilter(
        name="parent", queryset=Category.objects.all(), lookup_expr="exact")
    shop = django_filters.ModelChoiceFilter(
        name="shops", queryset=Shop.objects.all(), lookup_expr="exact")
    status = django_filters.ChoiceFilter(name="status", choices=CategoryStatus.choices, lookup_expr="exact")

    class Meta:
        model = Category
        fields = ["id", "parent", "shop", "identifier", "status"]


class CategoryViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a category by its ID.

    list: Lists all available categories.

    delete: Deletes a category.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new category.

    update: Fully updates an existing category.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing category.
    You can update only a set of attributes.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = CategoryFilter

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    def get_view_name(self):
        return _("Category")

    @classmethod
    def get_help_text(cls):
        return _("Categories can be listed, fetched, created, updated and deleted.")
