# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from shuup.core.utils.forms import RecoverPasswordForm


class SetPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()

    def validate(self, data):
        uidb64 = data.get("uidb64")
        token = data.get("token")
        password1 = data.get("new_password1")
        password2 = data.get("new_password2")
        user_model = get_user_model()

        if password1 != password2:
            raise serializers.ValidationError("Passwords do not match")

        try:
            uid = urlsafe_base64_decode(uidb64)
            user = user_model._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
            user = None

        if not user or not default_token_generator.check_token(user, token):
            raise serializers.ValidationError("The recovery link is invalid.")
        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password1"]
        user.set_password(new_password)
        user.save()


class SetAuthenticatedUserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()

    def validate(self, data):
        password1 = data.get("new_password1")
        password2 = data.get("new_password2")
        if password1 != password2:
            raise serializers.ValidationError("Passwords do not match")
        password = data.get("password")
        user = self.context["request"].user
        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid password")
        return data

    def save(self):
        user = self.context["request"].user
        new_password = self.validated_data["new_password1"]
        user.set_password(new_password)
        user.save()


class PasswordResetViewSet(GenericViewSet):
    serializer_class = serializers.BaseSerializer

    def create(self, request):
        form = RecoverPasswordForm(request.data)
        if form.is_valid():
            form.save(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class SetPasswordViewSet(GenericViewSet):
    serializer_class = serializers.BaseSerializer

    def create(self, request):
        if not request.user.is_anonymous():
            serializer = SetAuthenticatedUserPasswordSerializer(data=request.data, context={'request': request})
        else:
            serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": True}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
