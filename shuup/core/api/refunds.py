# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, serializers, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from shuup.api.fields import FormattedDecimalField
from shuup.core.excs import (
    InvalidRefundAmountException, NoRefundToCreateException,
    RefundExceedsAmountException, RefundExceedsQuantityException
)
from shuup.core.models import OrderLine, OrderLineType


class RefundLineSerializer(serializers.Serializer):
    line = serializers.PrimaryKeyRelatedField(queryset=OrderLine.objects.all())
    quantity = FormattedDecimalField()
    amount = FormattedDecimalField()
    restock_products = serializers.BooleanField()


class PartialRefundSerializer(serializers.Serializer):
    refund_lines = RefundLineSerializer(many=True, required=True)


class FullRefundSerializer(serializers.Serializer):
    restock_products = serializers.BooleanField()


class RefundMixin(object):
    @detail_route(methods=['post'])
    def create_refund(self, request, pk=None):
        order = self.get_object()

        if not order.can_create_refund():
            return Response(
                {"error": _("Order can not be refunded at the moment.")}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PartialRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        refund_data = []
        for refund_line_data in data["refund_lines"]:
            line = refund_line_data["line"]
            if line.order.id != order.id or line.type == OrderLineType.REFUND:
                return Response({"error": _("Can not refund line.")}, status=status.HTTP_400_BAD_REQUEST)

            refund_data.append({
                "line": line,
                "quantity": refund_line_data["quantity"],
                "amount": order.shop.create_price(refund_line_data["amount"]).amount,
                "restock_products": refund_line_data["restock_products"]
            })

        try:
            order.create_refund(refund_data, created_by=request.user)
        except InvalidRefundAmountException:
            raise exceptions.ValidationError(_("Invalid refund amount."))
        except RefundExceedsAmountException:
            raise exceptions.ValidationError(_("Refund exceeds amount."))
        except RefundExceedsQuantityException:
            raise exceptions.ValidationError(_("Refund exceeds quantity."))

        return Response({'success': _("Refund created.")}, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def create_full_refund(self, request, pk=None):
        order = self.get_object()

        if not order.can_create_refund():
            return Response(
                {"error": _("Order can not be refunded at the moment.")}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FullRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            order.create_full_refund(restock_products=data["restock_products"], created_by=request.user)
        except NoRefundToCreateException:
            raise exceptions.ValidationError(_("It is not possible to create the refund."))

        return Response({"success": _("Refund created.")}, status=status.HTTP_201_CREATED)
