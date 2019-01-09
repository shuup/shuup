# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from shuup.api.mixins import PermissionHelperMixin


class UserSerializer(ModelSerializer):

    class Meta:
        fields = "__all__"
        model = get_user_model()
        fields = "__all__"


class UserFilter(FilterSet):
    class Meta:
        model = get_user_model()
        fields = ['email']


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
