# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from shuup.api.mixins import (
    PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin
)
from shuup.core.models import ContactGroupPriceDisplay


class ContactGroupPriceDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ContactGroupPriceDisplay


class ContactGroupPriceDisplayViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, SearchableMixin, ModelViewSet):
    """
    retrieve: Fetches a contact group price display option by its ID.

    list: Lists all available contact group price display options.

    delete: Deletes a contact group price display option.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new contact group price display option.

    update: Fully updates an existing contact group price display option.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing contact group price display option.
    You can update only a set of attributes.
    """
    search_fields = SearchableMixin.search_fields + ("name",)
    queryset = ContactGroupPriceDisplay.objects.all()
    serializer_class = ContactGroupPriceDisplaySerializer

    def get_view_name(self):
        return _("Contact group price display")

    @classmethod
    def get_help_text(cls):
        return _("Contact group price display can be listed, fetched, created, updated and deleted.")
