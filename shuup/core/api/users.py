# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet


class UserSerializer(ModelSerializer):

    class Meta:
        model = get_user_model()


class UserFilter(FilterSet):
    class Meta:
        model = get_user_model()
        fields = ['email']


class UserViewSet(ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserFilter

    def get_view_name(self):
        return _("Users")

    def get_view_description(self, html=False):
        return _("Users can be listed, fetched, created, updated and deleted.")
