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
from shuup.core.models import SalesUnit


class SalesUnitSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=SalesUnit)

    class Meta:
        model = SalesUnit
        exclude = ("identifier",)


class SalesUnitViewSet(ProtectedModelViewSetMixin, ModelViewSet):
    queryset = SalesUnit.objects.all()
    serializer_class = SalesUnitSerializer

    def get_view_name(self):
        return _("Sales Unit")

    def get_view_description(self, html=False):
        return _("Sales units can be listed, fetched, created, updated and deleted.")
