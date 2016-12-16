# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from shuup.core.models import Manufacturer

from .mixins import ProtectedModelViewSetMixin


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        exclude = ("identifier",)
        extra_kwargs = {
            "created_on": {"read_only": True}
        }


class ManufacturerViewSet(ProtectedModelViewSetMixin, ModelViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer

    def get_view_name(self):
        return _("Manufacturer")

    def get_view_description(self, html=False):
        return _("Manufacturers can be listed, fetched, created, updated and deleted.")
