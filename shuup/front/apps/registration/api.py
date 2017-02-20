# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers, status
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.users import UserSerializer


class UserRegisterSerializer(UserSerializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=True, write_only=True)

    class Meta(UserSerializer.Meta):
        extra_kwargs = {
            "username": {"required": False}
        }

    def validate(self, data):
        user_model = get_user_model()
        if not data.get(user_model.USERNAME_FIELD) and not data.get("email"):
            raise serializers.ValidationError("username and/or email is required")
        # check if the username field is in user_data
        # if not, let's try "email" - it's not a good way to do that
        # but should fit almost any user model case
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


class FrontUserViewSet(PermissionHelperMixin, CreateModelMixin, GenericViewSet):
    """
    register: Register user
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserRegisterSerializer

    def get_view_name(self):
        return _("Front Users")

    @classmethod
    def get_help_text(cls):
        return _("Users can register to the storefront.")

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


def populate_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/front/user", FrontUserViewSet)
