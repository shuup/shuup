# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from math import pow

from django.db.models import Q, Sum
from django.template.loader import render_to_string

from shuup.core.models import (
    OrderLine, OrderLineType, OrderStatusRole, ShipmentProduct
)
from shuup.core.suppliers.base import StockAdjustmentType
from shuup.simple_supplier.forms import StockAdjustmentForm
from shuup.simple_supplier.models import StockAdjustment, StockCount


def get_current_stock_value(supplier_id, product_id):
    """
    Count stock values for supplier and product combination

    Logical count is events minus orders bought (not cancelled)
    describing how many products is currently orderable
    Physical count is events minus orders actually sent
    describing how many products is currently in stock

    :param supplier_id: supplier_id to count stock values for
    :param product_id: product_id to count stock values for
    :return: logical and physical count for product
    :rtype: dict
    """
    # TODO: Consider whether this should be done with an SQL view
    events = (
        StockAdjustment.objects
        .filter(supplier_id=supplier_id, product_id=product_id)
        .exclude(type=StockAdjustmentType.RESTOCK_LOGICAL)
        .aggregate(total=Sum("delta"))["total"] or 0)
    products_bought = (
        OrderLine.objects
        .filter(supplier_id=supplier_id, product_id=product_id)
        .exclude(
            Q(order__status__role=OrderStatusRole.CANCELED) |
            Q(type=OrderLineType.REFUND))
        .aggregate(total=Sum("quantity"))["total"] or 0)
    products_refunded_before_shipment = (
        StockAdjustment.objects
        .filter(supplier_id=supplier_id, product_id=product_id, type=StockAdjustmentType.RESTOCK_LOGICAL)
        .aggregate(total=Sum("delta"))["total"] or 0)
    products_sent = (
        ShipmentProduct.objects
        .filter(shipment__supplier=supplier_id, product_id=product_id)
        .aggregate(total=Sum("quantity"))["total"] or 0)

    return {
        "logical_count": events - products_bought + products_refunded_before_shipment,
        "physical_count": events - products_sent
    }


def get_stock_information_div_id(supplier, product):
    return "stock-information-%s-%s" % (supplier.id, product.id)


def get_stock_information_html(supplier, product):
    """
    Get html string to show current stock information for product

    :param supplier: shuup Supplier
    :type supplier: shuup.core.models.Supplier
    :param product: shuup Product
    :type product: shuup.core.models.Product
    :return: html div as a string
    :rtype: str
    """
    stock = StockCount.objects.filter(product=product, supplier=supplier).first()
    context = {
        "div_id": get_stock_information_div_id(supplier, product),
        "sales_decimals": product.sales_unit.decimals if product.sales_unit else 0,
        "sales_unit": product.sales_unit.short_name if product.sales_unit else "",
        "stock": stock
    }
    return render_to_string("shuup/simple_supplier/admin/stock_information.jinja", context)


def get_stock_adjustment_div(request, supplier, product):
    """
    Get html string to adjust stock values

    Contains inputs for purchase_price_value and delta

    :param request: HTTP request
    :type request: django.http.HttpRequest
    :param supplier: shuup Supplier
    :type supplier: shuup.core.models.Supplier
    :param product: shuup Product
    :type product: shuup.core.models.Product
    :return: html div as a string
    :rtype: str
    """
    latest_adjustment = StockAdjustment.objects.filter(
        product=product, supplier=supplier, type=StockAdjustmentType.INVENTORY).last()
    purchase_price = (latest_adjustment.purchase_price_value if latest_adjustment else Decimal("0.00"))
    context = {
        "product": product,
        "supplier": supplier,
        "delta_step": pow(0.1, product.sales_unit.decimals),
        "form": StockAdjustmentForm(initial={"purchase_price": purchase_price, "delta": None})
    }
    return render_to_string("shuup/simple_supplier/admin/add_stock_form.jinja", context=context, request=request)
