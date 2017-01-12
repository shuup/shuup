# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import serializers, status
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shuup.api.decorators import schema_serializer_class
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.contacts import PersonContactSerializer
from shuup.core.models import MutableAddress, PersonContact


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        # User model should be compliant to Django's AbstractBaseUser
        exclude = ["password"]
        model = get_user_model()


class UserFilter(FilterSet):
    class Meta:
        model = get_user_model()
        fields = ['email']


class PersonContactRegisterSerializer(PersonContactSerializer):
    shipping_address = AddressSerializer(required=False)
    billing_address = AddressSerializer(required=False)

    class Meta:
        model = PersonContact
        exclude = ["identifier", "default_shipping_address", "default_billing_address"]


class UserRegisterSerializer(UserSerializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=True, write_only=True)
    contact = PersonContactRegisterSerializer(required=True)

    class Meta(UserSerializer.Meta):
        username_field = get_user_model().USERNAME_FIELD
        extra_kwargs = {
            "username": {"required": False}
        }

    def create(self, validated_data):
        contact_data = validated_data.pop("contact")
        user_pwd = validated_data.pop("password")

        billing_address_data = contact_data.pop("billing_address", None)
        shipping_address_data = contact_data.pop("shipping_address", None)

        user_model = get_user_model()

        # check if the username field is in user_data
        # if not, let's try "email" - it's not a good way to do that
        # but should fit almost any user model case
        if user_model.USERNAME_FIELD not in validated_data and user_model.USERNAME_FIELD != "email":
            # try to get email from user, otherwise from person data
            email = validated_data.get("email", contact_data.get("email"))

            # use email as the username
            if email:
                validated_data[user_model.USERNAME_FIELD] = email

        user, created = get_user_model().objects.get_or_create(**validated_data)
        if not created:
            raise serializers.ValidationError("User already exists.")

        user.set_password(user_pwd)
        user.save()

        billing_address = None
        shipping_address = None

        if billing_address_data:
            billing_address = MutableAddress.from_data(billing_address_data)
            billing_address.full_clean()
            billing_address.save()

        if shipping_address_data:
            shipping_address = MutableAddress.from_data(shipping_address_data)
            shipping_address.full_clean()
            shipping_address.save()

        person = PersonContact(user=user,
                               default_billing_address=billing_address,
                               default_shipping_address=shipping_address,
                               **contact_data)
        person.full_clean()
        person.save()
        return person


class UserViewSet(PermissionHelperMixin, ModelViewSet):
    """
    retrieve: Fetches a user by its ID.

    list: Lists all users.

    delete: Deletes an user.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new user.

    update: Fully updates an existing user.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing user.
    You can update only a set of attributes.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserFilter

    def get_view_name(self):
        return _("Users")

    @classmethod
    def get_help_text(cls):
        return _("Users can be listed, fetched, created, updated and deleted.")

    @schema_serializer_class(UserRegisterSerializer)
    @list_route(methods=['post'])
    def register(self, request):
        """
        Register a User and a PersonContact.
        If the user information already exists, an error will be returned.
        """
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
