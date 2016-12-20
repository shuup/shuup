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
from rest_framework import viewsets

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import (
    Category, CategoryStatus, CategoryVisibility, Shop
)


class CategorySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Category)
    status = EnumField(CategoryStatus)
    visibility = EnumField(CategoryVisibility)

    class Meta:
        model = Category
        exclude = ("image",)


class CategoryFilter(FilterSet):
    parent = django_filters.ModelChoiceFilter(name="parent",
                                              queryset=Category.objects.all(),
                                              lookup_expr="exact")
    shop = django_filters.ModelChoiceFilter(name="shops",
                                            queryset=Shop.objects.all(),
                                            lookup_expr="exact")

    class Meta:
        model = Category
        fields = ["id", "parent", "shop"]


class CategoryViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a category by its ID.

    list: Lists all available categories.

    delete: Deletes a category.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new category.

    update: Fully updates an existing category.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existent category.
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
