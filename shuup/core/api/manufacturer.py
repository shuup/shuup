# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from shuup.api.mixins import (
    PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin
)
from shuup.core.models import Manufacturer
from shuup.core.shop_provider import get_shop


class ManufacturerSerializer(serializers.ModelSerializer):

    logo = serializers.SerializerMethodField()

    class Meta:
        model = Manufacturer
        exclude = ("identifier",)
        extra_kwargs = {
            "created_on": {"read_only": True}
        }

    def get_logo(self, manufacturer):
        if manufacturer.logo:
            return self.context["request"].build_absolute_uri(manufacturer.logo.url)


class ManufacturerViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin, ModelViewSet):
    """
    retrieve: Fetches a manufacturer by its ID.

    list: Lists all available manufacturers.

    delete: Deletes a manufacturer.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new manufacturer.

    update: Fully updates an existing manufacturer.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing manufacturer.
    You can update only a set of attributes.
    """
    search_fields = SearchableMixin.search_fields + ("name",)
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer

    def get_view_name(self):
        return _("Manufacturer")

    @classmethod
    def get_help_text(cls):
        return _("Manufacturers can be listed, fetched, created, updated and deleted.")

    def get_queryset(self):
        return self.queryset.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True))
