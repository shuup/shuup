# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import Contact, ContactGroup


class ContactGroupSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ContactGroup


class ContactSerializer(ModelSerializer):
    groups = ContactGroupSerializer(many=True, read_only=True)

    class Meta:
        fields = "__all__"
        model = Contact
        fields = "__all__"


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ['email', 'groups']


class ContactViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, ModelViewSet):
    """
    retrieve: Fetches a contact by its ID.

    list: Lists all available contacts.

    delete: Deletes a contact.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new contact.

    update: Fully updates an existing contact.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existent contact.
    You can update only a set of attributes.
    """

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = ContactFilter

    def get_view_name(self):
        return _("Contacts")

    @classmethod
    def get_help_text(cls):
        return _("Contacts can be listed, fetched, created, updated and deleted.")
