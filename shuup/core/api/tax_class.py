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

from shuup.api.mixins import ProtectedModelViewSetMixin
from shuup.core.models import TaxClass


class TaxClassSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=TaxClass)

    class Meta:
        model = TaxClass
        exclude = ("identifier",)


class TaxClassViewSet(ProtectedModelViewSetMixin, ModelViewSet):
    queryset = TaxClass.objects.all()
    serializer_class = TaxClassSerializer

    def get_view_name(self):
        return _("Tax Class")

    def get_view_description(self, html=False):
        return _("Tax classes can be listed, fetched, created, updated and deleted.")
