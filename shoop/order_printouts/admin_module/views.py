# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import Order, OrderLine, OrderLineType, Shipment
from shoop.order_printouts import pdf_export


def get_footer_information(shop):
    address = shop.contact_address
    if not address:
        return shop.name
    return "%s | %s %s, %s, %s | %s %s" % (
        shop.name,
        address.street,
        address.postal_code,
        address.city,
        address.country.name,
        address.phone,
        address.email
    )


def get_delivery_pdf(request, shipment_pk):
    shipment = Shipment.objects.get(pk=shipment_pk)
    order = shipment.order
    context = {
        "shipment": shipment,
        "order": order,
        "method_lines": OrderLine.objects.filter(
            order_id=order.id, type__in=[OrderLineType.PAYMENT, OrderLineType.SHIPPING]).order_by("ordering"),
        "today": datetime.date.today(),
        "header": "%s | %s | %s %s" % (_("Delivery slip"), order.shop.name, _("Order"), order.pk),
        "footer": get_footer_information(order.shop)
    }
    html = render_to_string("shoop/order_printouts/admin/delivery_pdf.jinja", context=context, request=request)
    return pdf_export.render_html_to_pdf(html)


def get_confirmation_pdf(request, order_pk):
    order = Order.objects.get(pk=order_pk)
    context = {
        "order": order,
        "today": datetime.date.today(),
        "header": "%s | %s | %s %s" % (_("Order confirmation"), order.shop.name, _("Order"), order.pk),
        "footer": get_footer_information(order.shop)
    }
    html = render_to_string("shoop/order_printouts/admin/confirmation_pdf.jinja", context=context, request=request)
    return pdf_export.render_html_to_pdf(html)
