# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
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
from rest_framework.fields import JSONField
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shuup.admin.modules.orders.json_order_creator import JsonOrderCreator
from shuup.admin.modules.orders.views.edit import encode_address
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.mixins import AvailableOrderMethodsMixin
from shuup.core.api.refunds import RefundMixin
from shuup.core.models import (
    Order, OrderLine, OrderStatus, OrderStatusRole, Payment
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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("payment_identifier", "amount_value", "description")


class OrderSerializer(AvailableOrderMethodsMixin, serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    payment_data = JSONField(read_only=True)
    shipping_data = JSONField(read_only=True)
    extra_data = JSONField(read_only=True)
    codes = JSONField(source='_codes', read_only=True)

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


class OrderStatusChangeMixin(object):
    def change_order_status(self, to_status):
        order = self.get_object()
        from_status = order.status
        if (
            to_status.role == OrderStatusRole.COMPLETE and not order.can_set_complete() or
            to_status.role == OrderStatusRole.CANCELED and not order.can_set_canceled()
        ):
            return Response({
                "status": "error",
                "errors": [{
                    "code": "invalid_status_change"
                }]
            }, status=status.HTTP_400_BAD_REQUEST)

        order.status = to_status
        order.save(update_fields=("status", "modified_on"))
        message = _("Order status changed: {from_status} to {to_status}").format(
            from_status=from_status, to_status=to_status)
        order.add_log_entry(message, user=self.request.user, identifier="status_change")
        return Response({"status": str(to_status)}, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def complete(self, request, pk=None):
        """ Set the order as Completed. """
        return self.change_order_status(OrderStatus.objects.get_default_complete())

    @detail_route(methods=['post'])
    def cancel(self, request, pk=None):
        """ Set the order as Canceled. """
        return self.change_order_status(OrderStatus.objects.get_default_canceled())


class OrderTaxesMixin(object):
    @detail_route(methods=['get'])
    def taxes(self, request, pk=None):
        """
        Get taxes for order
        """
        from shuup.core.api.tax import OrderLineTaxSerializer, TaxSummarySerializer
        order = self.get_object()
        tax_summary = order.get_tax_summary()
        rows = [row.to_dict() for row in tax_summary if row.tax_id]
        serializer = TaxSummarySerializer(data=rows, many=True)
        serializer.is_valid(True)
        lines = []
        for line in order.lines.filter(taxes__isnull=False):
            taxes = line.taxes.all()
            ts = OrderLineTaxSerializer(taxes, many=True, context=self.get_serializer_context())
            for row in ts.data:
                lines.append(row)
        return Response({
            "summary": serializer.validated_data,
            "lines": lines
        })


class OrderViewSet(PermissionHelperMixin,
                   ProtectedModelViewSetMixin,
                   OrderTaxesMixin,
                   OrderStatusChangeMixin,
                   RefundMixin,
                   ModelViewSet):
    """
    retrieve: Fetches an order by its ID.

    list: Lists all orders.

    delete: Deletes an order.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new order.

    update: Fully updates an existing order.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing order.
    You can update only a set of attributes.
    """

    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = OrderFilter

    def get_view_name(self):
        return _("Orders")

    @classmethod
    def get_help_text(cls):
        return _("Orders can be listed, fetched, created, updated and canceled.")

    def create(self, request, *args, **kwargs):
        post_data = request.data

        # Revise. We should not need to mutate the data for the serializer.
        # Also one problem is that we use text lines later at the create
        text_lines = set()
        for idx, line in enumerate(post_data.get("lines", [])):
            if "product" not in line:
                line["product"] = None
            if line.get("type") == "text":
                line["type"] = "other"
                text_lines.add(idx)

        request.data["orderer"] = None
        request.data["modified_by"] = None
        request.data["creator"] = request.user.pk

        for attr in ["shipping_method", "payment_method", "account_manager", "tax_group"]:
            if attr not in post_data:
                post_data[attr] = None

        if "customer_groups" not in post_data:
            post_data["customer_groups"] = []

        # Revise. Create should happen in the serializer, but then again
        # we need to return the errors from JsonOrderCreator in some sane way.
        serializer = self.get_serializer(data=post_data)
        serializer.is_valid(raise_exception=True)

        shop = serializer.validated_data["shop"]
        customer = serializer.validated_data["customer"]
        lines = [{
            "id": (idx + 1),
            "quantity": line["quantity"],
            "product": {
                "id": getattr(line["product"], "id", None)
            },
            "baseUnitPrice": line.get("base_unit_price_value"),
            "unitPrice": line.get("base_unit_price_value") if line["type"].label == "other" else None,
            "discountAmount": line.get("discount_amount_value", 0),
            "sku": line.get("sku"),
            "text": line.get("text"),
            "type": force_text(line["type"].label) if idx not in text_lines else "text"
        } for idx, line in enumerate(serializer.validated_data["lines"])]

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
                "shippingMethod": {"id": getattr(serializer.validated_data["shipping_method"], "id", None)},
                "paymentMethod": {"id": getattr(serializer.validated_data["payment_method"], "id", None)},
            },
            "lines": lines
        }
        if customer:
            data["customer"] = {
                "id": serializer.validated_data["customer"].id,
                "billingAddress": encode_address(customer.default_billing_address),
                "shippingAddress": encode_address(customer.default_shipping_address),
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

    @detail_route(methods=['post'])
    def create_payment(self, request, pk=None):
        """ Creates a payment for the order. """
        return _handle_payment_creation(request, self.get_object())

    @detail_route(methods=['post'])
    def set_fully_paid(self, request, pk=None):
        """ Set the order as Fully Paid. """
        order = self.get_object()
        if order.is_paid():
            return Response({"error": _("Order is already fully paid")})

        request.data["currency"] = order.currency
        request.data["amount_value"] = (order.taxful_total_price_value - order.get_total_paid_amount().value)
        return _handle_payment_creation(request, order)


def _handle_payment_creation(request, order):
    serializer = PaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    order.create_payment(
        Money(data["amount_value"], order.currency),
        data["payment_identifier"],
        data.get("description", "")
    )
    return Response({"success": _("Payment created")}, status=status.HTTP_201_CREATED)
