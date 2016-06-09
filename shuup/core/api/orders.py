# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.timezone import now
from rest_framework import serializers, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shuup.core.models import (
    MutableAddress, Order, OrderLine, OrderStatus, Payment
)
from shuup.utils.money import Money


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutableAddress


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("payment_identifier", "amount_value", "description")


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True, read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

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

    @detail_route(methods=['post'])
    def create_payment(self, request, pk=None):
        return _handle_payment_creation(request, self.get_object())

    @detail_route(methods=['post'])
    def set_fully_paid(self, request, pk=None):
        order = self.get_object()
        if order.is_paid():
            return Response({"status": "order is already fully paid"})

        request.data["currency"] = order.currency
        request.data["amount_value"] = (order.taxful_total_price_value - order.get_total_paid_amount().value)
        return _handle_payment_creation(request, order)


def _handle_payment_creation(request, order):
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        order.create_payment(
            Money(data["amount_value"], order.currency),
            data["payment_identifier"],
            data.get("description", "")
        )
        return Response({'status': 'payment created'}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
