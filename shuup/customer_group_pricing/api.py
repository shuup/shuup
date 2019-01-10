# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import django_filters
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import serializers, viewsets

from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.models import ContactGroup, Product, Shop
from shuup.customer_group_pricing.models import CgpPrice


class CgpPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = CgpPrice
        fields = "__all__"


class CgpPriceFilter(FilterSet):
    product = django_filters.ModelChoiceFilter(name="product",
                                               queryset=Product.objects.all(),
                                               lookup_expr="exact")
    shop = django_filters.ModelChoiceFilter(name="shop",
                                            queryset=Shop.objects.all(),
                                            lookup_expr="exact")
    group = django_filters.ModelChoiceFilter(name="group",
                                             queryset=ContactGroup.objects.all(),
                                             lookup_expr="exact")

    class Meta:
        model = CgpPrice
        fields = ["product", "shop", "group"]


class CgpPriceViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a customer group price by its ID.

    list: Lists all available customer group prices.

    delete: Deletes a customer group price.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new customer group price.

    update: Fully updates an existing customer group price.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing customer group price.
    You can update only a set of attributes.
    """

    queryset = CgpPrice.objects.all()
    serializer_class = CgpPriceSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = CgpPriceFilter

    def get_view_name(self):
        return _("Customer Group Price")

    @classmethod
    def get_help_text(cls):
        return _("Customer group prices can be listed, fetched, created, updated and deleted.")


def populate_customer_group_pricing_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/cgp_price", CgpPriceViewSet)
