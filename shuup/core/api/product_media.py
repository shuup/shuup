# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import mixins, serializers, viewsets

from shuup.api.fields import Base64FileField, EnumField
from shuup.api.mixins import PermissionHelperMixin
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


class ProductMediaViewSet(PermissionHelperMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    """
    retrieve: Fetches a product media by its ID.

    delete: Deletes a product media.
    If the object is related to another one and the relationship is protected, an error will be returned.

    update: Fully updates an existing product media.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing product media.
    You can update only a set of attributes.
    """

    queryset = ProductMedia.objects.all()
    serializer_class = ProductMediaSerializer

    def get_serializer_class(self):
        """ The serializer for upload must be the ProductMediaUploadSerializer """
        if self.request.method == "PUT":
            return ProductMediaUploadSerializer
        return super(ProductMediaViewSet, self).get_serializer_class()

    def get_view_name(self):
        return _("Product Media")

    @classmethod
    def get_help_text(cls):
        return _("Products media can be fetched, updated and deleted.")
