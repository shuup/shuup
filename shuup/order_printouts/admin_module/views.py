# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Order, OrderLine, OrderLineType, Shipment
from shuup.utils.pdf import html_to_pdf, render_html_to_pdf

from .forms import PrintoutsEmailForm


def get_delivery_pdf(request, shipment_pk):
    shipment = Shipment.objects.get(pk=shipment_pk)
    html = _get_delivery_html(request, shipment.order, shipment)
    return render_html_to_pdf(html, stylesheet_paths=["order_printouts/css/extra.css"])


def get_confirmation_pdf(request, order_pk):
    order = Order.objects.get(pk=order_pk)
    html = _get_confirmation_html(request, order)
    return render_html_to_pdf(html, stylesheet_paths=["order_printouts/css/extra.css"])


def send_delivery_email(request, shipment_pk):
    if request.method != "POST":
        raise Exception(_("Not allowed"))
    shipment = Shipment.objects.get(pk=shipment_pk)
    form = PrintoutsEmailForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        _send_printouts_email(
            [data["to"]], data["subject"], data["body"],
            _get_delivery_html(request, shipment.order, shipment), "delivery.pdf")
    return JsonResponse({"success": "OK!"})


def send_confirmation_email(request, order_pk):
    if request.method != "POST":
        raise Exception(_("Not allowed"))
    order = Order.objects.get(pk=order_pk)
    form = PrintoutsEmailForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        _send_printouts_email(
            [data["to"]], data["subject"], data["body"],
            _get_confirmation_html(request, order), "confirmation.pdf")
    return JsonResponse({"success": "OK!"})


def _get_delivery_html(request, order, shipment):
    context = {
        "shipment": shipment,
        "order": order,
        "method_lines": OrderLine.objects.filter(
            order_id=order.id, type__in=[OrderLineType.PAYMENT, OrderLineType.SHIPPING]).order_by("ordering"),
        "today": datetime.date.today(),
        "header": "%s | %s | %s %s" % (_("Delivery slip"), order.shop.name, _("Order"), order.pk),
        "footer": _get_footer_information(order.shop)
    }
    return render_to_string("shuup/order_printouts/admin/delivery_pdf.jinja", context=context, request=request)


def _get_confirmation_html(request, order):
    context = {
        "order": order,
        "today": datetime.date.today(),
        "header": "%s | %s | %s %s" % (_("Order confirmation"), order.shop.name, _("Order"), order.pk),
        "footer": _get_footer_information(order.shop)
    }
    return render_to_string("shuup/order_printouts/admin/confirmation_pdf.jinja", context=context, request=request)


def _get_footer_information(shop):
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


def _send_printouts_email(recipients, subject, body, html, attachment_filename):
    email = EmailMessage(subject=subject, body=body, to=recipients)
    pdf = html_to_pdf(html, stylesheet_paths=["order_printouts/css/extra.css"])
    email.attach(attachment_filename, pdf, mimetype="application/pdf")
    email.send()
