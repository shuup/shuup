# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import gettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import mixins, serializers, viewsets

from shuup.api.fields import Base64FileField, EnumField
from shuup.core.models import ProductMedia, ProductMediaKind
from shuup.utils.filer import filer_file_from_upload, filer_image_from_upload


class ProductMediaSerializer(TranslatableModelSerializer):
    kind = EnumField(enum=ProductMediaKind)
    translations = TranslatedFieldsField(shared_model=ProductMedia)
    file = serializers.SerializerMethodField()

    class Meta:
        model = ProductMedia
        extra_kwargs = {
            "product": {"read_only": True}
        }
        exclude = ("identifier",)

    def get_file(self, product_media):
        if product_media.file:
            return self.context["request"].build_absolute_uri(product_media.file.url)


class ProductMediaUploadSerializer(ProductMediaSerializer):
    file = Base64FileField(required=False, write_only=True)
    path = serializers.CharField(required=False, write_only=True)

    def create(self, validated_data):
        if "path" in validated_data:
            validated_data.pop("path")
        return super(ProductMediaUploadSerializer, self).create(validated_data)

    def validate(self, data):
        if not (data.get("file") or data.get("external_url")):
            raise serializers.ValidationError("You may set either `file` or `external_url`.")
        elif data.get("file"):
            if not data.get("path"):
                raise serializers.ValidationError("`path` is required when `file` is set.")
            elif not data["file"].content_type.startswith("image/") and data["kind"] != ProductMediaKind.IMAGE:
                raise serializers.ValidationError("Kind must be IMAGE for this content type.")

            # changes the filer function according to the media type
            filer_func = filer_image_from_upload if data["kind"] == ProductMediaKind.IMAGE else filer_file_from_upload
            # overrides the file with the correct file generated from filer
            data["file"] = filer_func(self.context["request"], path=data["path"], upload_data=data["file"])

        return data

    class Meta:
        model = ProductMedia
        extra_kwargs = {
            "product": {"read_only": True}
        }
        exclude = ("identifier",)


class ProductMediaViewSet(mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    queryset = ProductMedia.objects.none()
    serializer_class = ProductMediaSerializer

    def get_queryset(self):
        if getattr(self.request.user, 'is_superuser', False):
            return ProductMedia.objects.all()
        else:
            return ProductMedia.objects.filter(shops=self.request.shop)

    def get_serializer_class(self):
        """ The serializer for upload must be the ProductMediaUploadSerializer """
        if self.request.method == "PUT":
            return ProductMediaUploadSerializer
        return super(ProductMediaViewSet, self).get_serializer_class()

    def get_view_name(self):
        return _("Product Media")

    def get_view_description(self, html=False):
        return _("Products media can be listed, fetched, updated and deleted.")
