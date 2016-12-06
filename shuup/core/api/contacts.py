# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from shuup.core.models import Contact, ContactGroup


class ContactGroupSerializer(ModelSerializer):
    class Meta:
        model = ContactGroup


class ContactSerializer(ModelSerializer):
    groups = ContactGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Contact


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ['email', 'groups']


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = ContactFilter
