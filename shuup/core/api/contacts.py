# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.models import Contact, ContactGroup, Gender, PersonContact


class ContactGroupSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ["members"]
        model = ContactGroup


class ContactSerializer(serializers.ModelSerializer):
    groups = ContactGroupSerializer(many=True, read_only=True)
    default_shipping_address = AddressSerializer(required=False)
    default_billing_address = AddressSerializer(required=False)

    class Meta:
        model = Contact
        exclude = ["identifier"]
        extra_kwargs = {
            "created_on": {"read_only": True}
        }


class PersonContactSerializer(ContactSerializer):
    gender = EnumField(Gender, required=False)

    class Meta(ContactSerializer.Meta):
        model = PersonContact
        extra_kwargs = {
            "created_on": {"read_only": True}
        }


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

    partial_update: Updates an existing contact.
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


class PersonContactViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, ModelViewSet):
    """
    retrieve: Fetches a person contact by its ID.

    list: Lists all available person contacts.

    delete: Deletes a person contact.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new person contact.

    update: Fully updates an existing person contact.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing person contact.
    You can update only a set of attributes.
    """

    queryset = PersonContact.objects.all()
    serializer_class = PersonContactSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = ContactFilter

    def get_view_name(self):
        return _("Person Contact")

    @classmethod
    def get_help_text(cls):
        return _("Person Contacts can be listed, fetched, created, updated and deleted.")
