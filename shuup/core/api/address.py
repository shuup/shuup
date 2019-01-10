# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, serializers
from rest_framework.viewsets import GenericViewSet

from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import MutableAddress


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutableAddress
        fields = "__all__"
        extra_kwargs = settings.SHUUP_ADDRESS_FIELD_PROPERTIES


class MutableAddressViewSet(PermissionHelperMixin,
                            ProtectedModelViewSetMixin,
                            mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            GenericViewSet):
    """
    retrieve: Fetches an address by its ID.

    delete: Deletes an address.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new address.

    update: Fully updates an existing address.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing address.
    You can update only a set of attributes.
    """

    queryset = MutableAddress.objects.all()
    serializer_class = AddressSerializer

    def get_view_name(self):
        return _("Mutable Address")

    @classmethod
    def get_help_text(cls):
        return _("Mutable Addressess can be fetched, created, updated and deleted.")
