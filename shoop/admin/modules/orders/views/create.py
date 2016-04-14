# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import json

from babel.numbers import format_decimal
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http.response import HttpResponse, JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django_countries import countries

from shoop.admin.modules.orders.json_order_creator import JsonOrderCreator
from shoop.core.models import (
    AnonymousContact, CompanyContact, Contact, Order, PaymentMethod, Product,
    ShippingMethod, Shop, ShopStatus
)
from shoop.core.pricing import get_pricing_module
from shoop.utils.i18n import (
    format_money, format_percent, get_current_babel_locale
)


def create_order_from_state(state, **kwargs):
    joc = JsonOrderCreator()
    order = joc.create_order_from_state(state, **kwargs)
    if not order:
        raise ValidationError(list(joc.errors))
    return order


def create_source_from_state(state, **kwargs):
    joc = JsonOrderCreator()
    source = joc.create_source_from_state(state, **kwargs)
    if not source:
        raise ValidationError(list(joc.errors))
    return source


def encode_address(address):
    if not address:
        return {}
    return json.loads(serializers.serialize("json", [address]))[0].get("fields")


def encode_shop(shop):
    return {
        "id": shop.pk,
        "name": force_text(shop),
        "currency": shop.currency,
        "pricesIncludeTaxes": shop.prices_include_tax
    }


def encode_method(method):
    basic_data = {"id": method.pk, "name": force_text(method)}
    return basic_data


def encode_line(line):
    return {
        "sku": line.sku,
        "text": line.text,
        "quantity": format_decimal(line.quantity, locale=get_current_babel_locale()),
        "unitPrice": format_money(line.base_unit_price.amount),
        "discountAmount": format_money(line.discount_amount.amount),
        "taxlessTotal": format_money(line.taxless_price.amount),
        "taxPercentage": format_percent(line.tax_rate, 2),
        "taxfulTotal": format_money(line.taxful_price.amount)
    }


def get_price_info(shop, customer, product, quantity):
    """
    Get price info of given product for given context parameters.

    :type shop: shoop.core.models.Shop
    :type customer: shoop.core.models.Contact
    :type product: shoop.core.models.Product
    :type quantity: numbers.Number
    """
    pricing_mod = get_pricing_module()
    pricing_ctx = pricing_mod.get_context_from_data(
        shop=shop,
        customer=(customer or AnonymousContact()),
    )
    return pricing_mod.get_price_info(pricing_ctx, product, quantity=quantity)


class OrderCreateView(TemplateView):
    model = Order
    template_name = "shoop/admin/orders/create.jinja"
    context_object_name = "order"
    title = _("Create Order")

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView, self).get_context_data(**kwargs)
        context["config"] = self.get_config()
        return context

    def get_config(self):
        shops = [encode_shop(shop) for shop in Shop.objects.filter(status=ShopStatus.ENABLED)]
        shipping_methods = ShippingMethod.objects.enabled()
        payment_methods = PaymentMethod.objects.enabled()
        return {
            "shops": shops,
            "countries": [{"id": code, "name": name} for code, name in list(countries)],
            "shippingMethods": [encode_method(sm) for sm in shipping_methods],
            "paymentMethods": [encode_method(pm) for pm in payment_methods]
        }

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("command"):
            return self.dispatch_command(request)
        return super(OrderCreateView, self).dispatch(request, *args, **kwargs)

    def dispatch_command(self, request):
        handler = getattr(self, "handle_%s" % request.GET.get("command"), None)
        if not callable(handler):
            return JsonResponse({"error": "unknown command %s" % request.GET.get("command")}, status=400)
        retval = handler(request)
        if not isinstance(retval, HttpResponse):
            retval = JsonResponse(retval)
        return retval

    def handle_product_data(self, request):
        product_id = request.GET["id"]
        shop_id = request.GET["shop_id"]
        customer_id = request.GET.get("customer_id")
        quantity = decimal.Decimal(request.GET.get("quantity", 1))
        already_in_lines_qty = decimal.Decimal(request.GET.get("already_in_lines_qty", 0))
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return {"errorText": _("Product %s does not exist.") % product_id}
        shop = Shop.objects.get(pk=shop_id)
        try:
            shop_product = product.get_shop_instance(shop)
        except ObjectDoesNotExist:
            return {
                "errorText": _("Product %(product)s is not available in the %(shop)s shop.") %
                {"product": product.name, "shop": shop.name}
            }

        min_quantity = shop_product.minimum_purchase_quantity
        # Make quantity to be at least minimum quantity
        quantity = (min_quantity if quantity < min_quantity else quantity)
        customer = Contact.objects.filter(pk=customer_id).first() if customer_id else None
        price_info = get_price_info(shop, customer, product, quantity)
        supplier = shop_product.suppliers.first()  # TODO: Allow setting a supplier?
        errors = " ".join(
            [str(message.args[0]) for message in shop_product.get_orderability_errors(
                supplier=supplier, quantity=(quantity + already_in_lines_qty), customer=customer, ignore_minimum=True)])
        return {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "quantity": quantity,
            "purchaseMultiple": shop_product.purchase_multiple,
            "errors": errors,
            "taxClass": {
                "id": product.tax_class.id,
                "name": force_text(product.tax_class),
            },
            "baseUnitPrice": {
                "value": price_info.base_price.value,
                "includesTax": price_info.base_price.includes_tax
            },
            "unitPrice": {
                "value": price_info.price.value,
                "includesTax": price_info.price.includes_tax
            }
        }

    def handle_customer_data(self, request):
        customer_id = request.GET["id"]
        customer = Contact.objects.filter(pk=customer_id).first()
        if not customer:
            return JsonResponse(
                {"success": False, "errorMessage": _("Contact %s does not exist.") % customer_id}, status=400
            )
        return {
            "id": customer.id,
            "name": customer.name,
            "isCompany": bool(isinstance(customer, CompanyContact)),
            "billingAddress": encode_address(customer.default_billing_address),
            "shippingAddress": encode_address(customer.default_shipping_address)
        }

    @transaction.atomic
    def _handle_source_data(self, request):
        state = json.loads(request.body.decode("utf-8"))["state"]
        source = create_source_from_state(
            state,
            creator=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        # Calculate final lines for confirmation
        source.calculate_taxes(force_recalculate=True)
        return {
            "taxfulTotal": format_money(source.taxful_total_price.amount),
            "taxlessTotal": format_money(source.taxless_total_price.amount),
            "totalDiscountAmount": format_money(source.total_discount.amount),
            "orderLines": [encode_line(line) for line in source.get_final_lines(with_taxes=True)],
            "billingAddress": source.billing_address.as_string_list() if source.billing_address else None,
            "shippingAddress": source.shipping_address.as_string_list() if source.shipping_address else None,
        }

    @transaction.atomic
    def _handle_create(self, request):
        state = json.loads(request.body.decode("utf-8"))["state"]
        order = create_order_from_state(
            state,
            creator=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.success(request, _("Order %(identifier)s created.") % vars(order))
        return JsonResponse({
            "success": True,
            "orderIdentifier": order.identifier,
            "url": reverse("shoop_admin:order.list")
        })

    def handle_source_data(self, request):
        return _handle_or_return_error(self._handle_source_data, request, _("Could not proceed with order:"))

    def handle_create(self, request):
        return _handle_or_return_error(self._handle_create, request, _("Could not create order:"))


def _handle_or_return_error(func, request, error_message):
    try:
        return func(request)
    except Exception as exc:
        if isinstance(exc, ValidationError):
            error_message += "\n" + "\n".join(force_text(err) for err in exc.messages)
        else:
            error_message += " {}".format(exc)
        return JsonResponse({"success": False, "errorMessage": error_message}, status=400)
