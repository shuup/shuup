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
from rest_framework.viewsets import ModelViewSet

from shuup.api.fields import EnumField
from shuup.core.models import Attribute, AttributeType, AttributeVisibility


class AttributeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Attribute)
    type = EnumField(enum=AttributeType)
    visibility_mode = EnumField(enum=AttributeVisibility)

    class Meta:
        fields = "__all__"
        model = Attribute


class AttributeViewSet(ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer

    def get_view_name(self):
        return _("Attributes")

    def get_view_description(self, html=False):
        return _("Attributes can be listed, fetched, created, updated and deleted.")
