# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework.viewsets import ModelViewSet

from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import SalesUnit


class SalesUnitSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=SalesUnit)

    class Meta:
        model = SalesUnit
        exclude = ("identifier",)


class SalesUnitViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, ModelViewSet):
    """
    retrieve: Fetches a sales unit by its ID.

    list: Lists all available sales units.

    delete: Deletes a sales unit.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new sales unit.

    update: Fully updates an existing sales unit.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing sales unit.
    You can update only a set of attributes.
    """

    queryset = SalesUnit.objects.all()
    serializer_class = SalesUnitSerializer

    def get_view_name(self):
        return _("Sales Unit")

    @classmethod
    def get_help_text(cls):
        return _("Sales units can be listed, fetched, created, updated and deleted.")
