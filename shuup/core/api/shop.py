# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import viewsets

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import Shop, ShopStatus


class ShopSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Shop)
    status = EnumField(ShopStatus)

    class Meta:
        model = Shop
        exclude = ("logo", "favicon")


class ShopViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a shop by its ID.

    list: Lists all available shops.

    delete: Deletes a shop.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new shop.

    update: Fully updates an existing shop.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing shop.
    You can update only a set of attributes.
    """

    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

    def get_view_name(self):
        return _("Shop")

    @classmethod
    def get_help_text(cls):
        return _("Shops can be listed, fetched, created, updated and deleted.")
