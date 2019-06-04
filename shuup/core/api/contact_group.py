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

from shuup.api.mixins import (
    PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin
)
from shuup.core.models import ContactGroup
from shuup.core.shop_provider import get_shop


class ContactGroupSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=ContactGroup)

    class Meta:
        fields = "__all__"
        model = ContactGroup


class ContactGroupViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin, ModelViewSet):
    """
    retrieve: Fetches a contact groups by its ID.

    list: Lists all available contact groups.

    delete: Deletes a contact group.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new contact group.

    update: Fully updates an existing contact group.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing contact group.
    You can update only a set of attributes.
    """
    search_fields = SearchableMixin.search_fields + ("name",)
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer

    def get_view_name(self):
        return _("Contact group")

    @classmethod
    def get_help_text(cls):
        return _("Contact group can be listed, fetched, created, updated and deleted.")

    def get_queryset(self):
        return self.queryset.filter(shop=get_shop(self.request))
