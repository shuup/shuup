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

from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import TaxClass


class TaxClassSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=TaxClass)

    class Meta:
        model = TaxClass
        exclude = ("identifier",)


class TaxClassViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, ModelViewSet):
    """
    retrieve: Fetches a tax class by its ID.

    list: Lists all available tax classes.

    delete: Deletes a tax class.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new tax class.

    update: Fully updates an existing tax class.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing tax class.
    You can update only a set of attributes.
    """

    queryset = TaxClass.objects.all()
    serializer_class = TaxClassSerializer

    def get_view_name(self):
        return _("Tax Class")

    @classmethod
    def get_help_text(cls):
        return _("Tax classes can be listed, fetched, created, updated and deleted.")
