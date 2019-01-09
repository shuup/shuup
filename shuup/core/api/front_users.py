# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, status
from rest_framework.mixins import (
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.models import (
    Gender, get_person_contact, MutableAddress, PersonContact
)


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("password", "email", "username")
        extra_kwargs = {
            "password": {"required": True, "write_only": True}
        }

    def validate(self, data):
        user_model = get_user_model()
        if not data.get(user_model.USERNAME_FIELD) and not data.get("email"):
            raise serializers.ValidationError("username and/or email is required")
        if user_model.USERNAME_FIELD not in data and user_model.USERNAME_FIELD != "email":
            email = data.get("email")
            if email:
                data[user_model.USERNAME_FIELD] = email

        pwd = data.pop("password")
        if user_model.objects.filter(**data).exists():
            raise serializers.ValidationError("User already exists.")
        data["password"] = pwd
        return data

    def create(self, validated_data):
        user_pwd = validated_data.pop("password")
        user = get_user_model()(**validated_data)
        user.set_password(user_pwd)
        user.save()
        return user


class ContactSerializer(serializers.ModelSerializer):
    default_shipping_address = AddressSerializer(required=False)
    default_billing_address = AddressSerializer(required=False)
    gender = EnumField(Gender, required=False)
    name = serializers.CharField(required=False)

    class Meta:
        model = PersonContact
        exclude = ["identifier", "tax_group", "polymorphic_ctype", "account_manager"]
        extra_kwargs = {
            "created_on": {"read_only": True}
        }

    def update_address(self, instance, field_name, validated_address_data):
        if not validated_address_data:
            return None
        contact_address = getattr(instance, field_name)
        if contact_address:
            MutableAddress.objects.filter(pk=contact_address.pk).update(**validated_address_data)
            contact_address.refresh_from_db()
        else:
            address = MutableAddress(**validated_address_data)
            address.save()
            setattr(instance, field_name, address)
            instance.save()

    def update(self, instance, validated_data):
        default_shipping_address = validated_data.pop("default_shipping_address", None)
        default_billing_address = validated_data.pop("default_billing_address", None)
        instance = super(ContactSerializer, self).update(instance, validated_data)
        self.update_address(instance, "default_shipping_address", default_shipping_address)
        self.update_address(instance, "default_billing_address", default_billing_address)
        return instance


class FrontUserViewSet(PermissionHelperMixin, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    register: Register user

    retrieve: Fetches the current contact.

    update: Updates the current contact.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing contact.
    You can update only a set of attributes.
    """

    queryset = get_user_model().objects.all()
    serializer_class = UserRegisterSerializer

    def get_view_name(self):
        return _("Front Users")

    @classmethod
    def get_help_text(cls):
        return _("Users can register to the storefront and fetch and update their own user details.")

    def get_object(self):
        if self.request.user.is_anonymous():
            raise Http404
        return get_person_contact(self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        else:
            return ContactSerializer

    def create(self, request, *args, **kwargs):
        """
        Register a User.
        If the user information already exists, an error will be returned.
        """
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            auth_classes = getattr(settings, "REST_FRAMEWORK", {}).get("DEFAULT_AUTHENTICATION_CLASSES", [])
            # TODO: ultimately should have a configurable "preferred" auth method
            if "rest_framework_jwt.authentication.JSONWebTokenAuthentication" in auth_classes:
                username_field = get_user_model().USERNAME_FIELD
                username = serializer.data.get(username_field)
                password = request.data.get("password")
                token_data = {"password": password}
                token_data[username_field] = username
                token_serializer = JSONWebTokenSerializer(data=token_data)
                if token_serializer.is_valid():
                    return Response({"token": token_serializer.object.get('token')}, status=status.HTTP_201_CREATED)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
