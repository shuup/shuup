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
from rest_framework.viewsets import ModelViewSet

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.models import Attribute, AttributeType, AttributeVisibility


class AttributeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Attribute)
    type = EnumField(enum=AttributeType)
    visibility_mode = EnumField(enum=AttributeVisibility)

    class Meta:
        fields = "__all__"
        model = Attribute


class AttributeViewSet(PermissionHelperMixin, ModelViewSet):
    """
    retrieve: Fetches an attribute by its ID.

    list: Lists all available attributes.

    delete: Deletes an attribute.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new attribute.

    update: Fully updates an existing attribute.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing attribute.
    You can update only a set of attributes.
    """

    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer

    def get_view_name(self):
        return _("Attributes")

    @classmethod
    def get_help_text(cls):
        return _("Attributes can be listed, fetched, created, updated and deleted.")
