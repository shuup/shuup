# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_filters import DateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import serializers, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shuup.admin.modules.orders.json_order_creator import JsonOrderCreator
from shuup.admin.modules.orders.views.edit import encode_address
from shuup.core.models import (
    Contact, MutableAddress, Order, OrderLine, OrderStatus, Payment, Shop
)
from shuup.utils.money import Money


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ("product", "sku", "text", "quantity", "type", "base_unit_price_value", "discount_amount_value")

    def get_fields(self):
        fields = super(OrderLineSerializer, self).get_fields()
        fields["text"].required = False
        return fields


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutableAddress
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("payment_identifier", "amount_value", "description")


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def get_fields(self):
        fields = super(OrderSerializer, self).get_fields()
        for name, field in fields.items():
            if name in ("status", "key", "label", "currency"):
                field.required = False
            if name == "order_date":
                field.default = lambda: now()
            if name == "status":
                field.default = OrderStatus.objects.get_default_initial()
            if name in ("shipping_method", "payment_method", "customer"):
                field.required = True
        return fields


class OrderFilter(FilterSet):
    date = DateTimeFilter(name="order_date", method="filter_date")

    def filter_date(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(order_date__year=value.year, order_date__month=value.month, order_date__day=value.day)

    class Meta:
        model = Order
        fields = ["identifier", "date", "status"]


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = OrderFilter

    def get_view_name(self):
        return _("Orders")

    def get_view_description(self, html=False):
        return _("Orders can be listed, fetched, created, updated and canceled.")

    def create(self, request, *args, **kwargs):
        text_lines = set()
        for idx, line in enumerate(request.data.get("lines", [])):
            if "product" not in line:
                line["product"] = None
            if line.get("type") == "text":
                line["type"] = "other"
                text_lines.add(idx)
        request.data["orderer"] = None
        request.data["modified_by"] = None
        request.data["creator"] = request.user.pk
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shop = Shop.objects.get(pk=serializer.data["shop"])
        customer = Contact.objects.get(pk=serializer.data["customer"])
        lines = [{
            "id": (idx + 1),
            "quantity": line["quantity"],
            "product": {
                "id": line["product"]
            },
            "baseUnitPrice": line.get("base_unit_price_value"),
            "unitPrice": line.get("base_unit_price_value") if line["type"].label == "other" else None,
            "discountAmount": line.get("discount_amount_value", 0),
            "sku": line.get("sku"),
            "text": line.get("text"),
            "type": force_text(line["type"].label) if idx not in text_lines else "text"
        } for idx, line in enumerate(serializer.data["lines"])]

        data = {
            "shop": {
                "selected": {
                    "id": shop.id,
                    "name": shop.name,
                    "currency": shop.currency,
                    "priceIncludeTaxes": shop.prices_include_tax
                }
            },
            "methods": {
                "shippingMethod": {"id": serializer.data["shipping_method"]},
                "paymentMethod": {"id": serializer.data["payment_method"]},
            },
            "customer": {
                "id": serializer.data["customer"],
                "billingAddress": encode_address(customer.default_billing_address),
                "shippingAddress": encode_address(customer.default_shipping_address),
            },
            "lines": lines
        }
        joc = JsonOrderCreator()
        order = joc.create_order_from_state(data, creator=request.user)
        if not order:
            return JsonResponse({
                "status": "error",
                "errors": [{
                    "message": err.message,
                    "code": err.code
                } for err in joc.errors]
            }, status=400)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['put'])
    def complete(self, request, pk=None):
        order = self.get_object()
        if not order.can_set_complete():
            return Response({
                "status": "error",
                "errors": [{
                    "message": "Cannot complete order",
                    "code": "invalid_status_change"
                }]
            }, status=status.HTTP_400_BAD_REQUEST)
        order.status = OrderStatus.objects.get_default_complete()
        order.save(update_fields=("status",))
        return Response({"status": "order marked complete"}, status=status.HTTP_200_OK)

    @detail_route(methods=['put'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if not order.can_set_canceled():
            return Response({
                "status": "error",
                "errors": [{
                    "message": "Cannot cancel order",
                    "code": "invalid_status_change"
                }]
            }, status=status.HTTP_400_BAD_REQUEST)
        order.set_canceled()
        return Response({"status": "order canceled"}, status=status.HTTP_200_OK)

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
