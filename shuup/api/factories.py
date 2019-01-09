# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from parler.models import TranslatableModel
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import permissions, serializers, viewsets


def serializer_factory(model, serializer_class=None, attrs=None, meta=None):
    attrs = attrs or {}
    meta = meta or {}
    if not serializer_class:
        if issubclass(model, TranslatableModel):
            serializer_class = TranslatableModelSerializer
            attrs["translations"] = TranslatedFieldsField(shared_model=model)
        else:
            serializer_class = serializers.ModelSerializer
    meta.setdefault("model", model)
    meta.setdefault("fields", "__all__")
    attrs.setdefault("Meta", type(str("Meta"), (object,), meta))
    return type(str("%sSerializer" % model.__name__), (serializer_class,), attrs)


def viewset_factory(model, viewset_class=viewsets.ModelViewSet, **attrs):
    attrs.setdefault("permission_classes", (permissions.IsAdminUser,))
    attrs.setdefault("queryset", model.objects.all())
    if not attrs.get("serializer_class"):
        attrs["serializer_class"] = serializer_factory(model)
    return type(str("%sViewSet" % model.__name__), (viewset_class,), attrs)
