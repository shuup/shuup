# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Order, OrderLine, OrderLineType, Shipment
from shuup.utils.excs import Problem
from shuup.utils.pdf import html_to_pdf, render_html_to_pdf

from .forms import PrintoutsEmailForm


def validate_shop_for_order(request, order):
    if get_shop(request) != order.shop:
        raise Problem(
            _("The current shop doesn't match the order shop. Please change to the shop that is currently active.")
        )


def get_delivery_pdf(request, shipment_pk):
    shipment = Shipment.objects.get(pk=shipment_pk)
    validate_shop_for_order(request, shipment.order)
    html = _get_delivery_html(request, shipment.order, shipment)
    return render_html_to_pdf(html, stylesheet_paths=["order_printouts/css/extra.css"])


def get_confirmation_pdf(request, order_pk):
    order = Order.objects.get(pk=order_pk)
    validate_shop_for_order(request, order)
    html = _get_confirmation_html(request, order)
    return render_html_to_pdf(html, stylesheet_paths=["order_printouts/css/extra.css"])


def get_delivery_html(request, shipment_pk):
    shipment = Shipment.objects.get(pk=shipment_pk)
    validate_shop_for_order(request, shipment.order)
    return HttpResponse(_get_delivery_html(request, shipment.order, shipment, True))


def get_confirmation_html(request, order_pk):
    order = Order.objects.get(pk=order_pk)
    validate_shop_for_order(request, order)
    return HttpResponse(_get_confirmation_html(request, order, True))


def send_delivery_email(request, shipment_pk):
    if request.method != "POST":
        raise Exception(_("Non-POST request methods are forbidden."))
    shipment = Shipment.objects.get(pk=shipment_pk)
    validate_shop_for_order(request, shipment.order)
    form = PrintoutsEmailForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        _send_printouts_email(
            [data["to"]], data["subject"], data["body"],
            _get_delivery_html(request, shipment.order, shipment), "delivery.pdf")
    return JsonResponse({"success": "Success!"})


def send_confirmation_email(request, order_pk):
    if request.method != "POST":
        raise Exception(_("Non-POST request methods are forbidden."))
    order = Order.objects.get(pk=order_pk)
    validate_shop_for_order(request, order)
    form = PrintoutsEmailForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        _send_printouts_email(
            [data["to"]], data["subject"], data["body"],
            _get_confirmation_html(request, order), "confirmation.pdf")
    return JsonResponse({"success": "Success!"})


def _get_delivery_html(request, order, shipment, html_mode=False):
    context = {
        "shipment": shipment,
        "order": order,
        "method_lines": OrderLine.objects.filter(
            order_id=order.id, type__in=[OrderLineType.PAYMENT, OrderLineType.SHIPPING]).order_by("ordering"),
        "today": datetime.date.today(),
        "header": "%s | %s | %s %s" % (_("Delivery slip"), order.shop.name, _("Order"), order.pk),
        "footer": _get_footer_information(order.shop),
        "html_mode": html_mode
    }

    provided_information = {}
    for provided_info in sorted(get_provide_objects("order_printouts_delivery_extra_fields")):
        info = provided_info(order, shipment)
        if info.provides_extra_fields():
            provided_information.update(info.extra_fields)
    context['extra_fields'] = provided_information

    return render_to_string("shuup/order_printouts/admin/delivery_pdf.jinja", context=context, request=request)


def _get_confirmation_html(request, order, html_mode=False):
    context = {
        "order": order,
        "today": datetime.date.today(),
        "header": "%s | %s | %s %s" % (_("Order confirmation"), order.shop.name, _("Order"), order.pk),
        "footer": _get_footer_information(order.shop),
        "html_mode": html_mode
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
