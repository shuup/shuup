# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.timezone import now
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from shoop.core.models import MutableAddress, Order, OrderLine, OrderStatus


class OrderLineSerializer(ModelSerializer):
    class Meta:
        model = OrderLine


class AddressSerializer(ModelSerializer):
    class Meta:
        model = MutableAddress


class OrderSerializer(ModelSerializer):
    lines = OrderLineSerializer(many=True, read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)

    def get_fields(self):
        fields = super(OrderSerializer, self).get_fields()
        for name, field in fields.items():
            if name in ("status", "key", "label"):
                field.required = False
            if name == "order_date":
                field.default = lambda: now()
        return fields

    def create(self, validated_data):
        if not validated_data.get("status"):
            validated_data["status"] = OrderStatus.objects.get_default_initial()
        return super(OrderSerializer, self).create(validated_data)

    class Meta:
        model = Order


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
