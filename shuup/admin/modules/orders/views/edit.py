# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import json

from babel.numbers import format_currency, format_decimal
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Sum
from django.http.response import HttpResponse, JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django_countries import countries

from shuup.admin.modules.orders.json_order_creator import JsonOrderCreator
from shuup.admin.toolbar import Toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import (
    AnonymousContact, CompanyContact, Contact, Order, OrderLineType,
    PaymentMethod, PersonContact, Product, ShippingMethod, Shop, ShopStatus
)
from shuup.core.pricing import get_pricing_module
from shuup.utils.i18n import (
    format_money, format_percent, get_current_babel_locale,
    get_locally_formatted_datetime
)


def create_order_from_state(state, **kwargs):
    joc = JsonOrderCreator()
    order = joc.create_order_from_state(state, **kwargs)
    if not order:
        raise ValidationError(list(joc.errors))
    return order


def update_order_from_state(state, order_to_update, **kwargs):
    joc = JsonOrderCreator()
    order = joc.update_order_from_state(state, order_to_update, **kwargs)
    if not order:
        raise ValidationError(list(joc.errors))
    return order


def create_source_from_state(state, **kwargs):
    joc = JsonOrderCreator()
    source = joc.create_source_from_state(state, **kwargs)
    if not source:
        raise ValidationError(list(joc.errors))
    return source


def encode_address(address, tax_number=""):
    if not address:
        return {"tax_number": tax_number}
    address_dict = json.loads(serializers.serialize("json", [address]))[0].get("fields")
    address_dict.setdefault("tax_number", tax_number)
    return address_dict


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


def get_line_data_for_edit(shop, line):
    total_price = line.taxful_price.value if shop.prices_include_tax else line.taxless_price.value
    base_data = {
        "id": line.id,
        "type": "other" if line.quantity else "text",
        "text": line.text,
        "quantity": line.quantity,
        "sku": line.sku,
        "baseUnitPrice": line.base_unit_price.value,
        "unitPrice": total_price / line.quantity if line.quantity else 0,
        "unitPriceIncludesTax": shop.prices_include_tax,
        "errors": "",
        "step": ""
    }
    if line.product:
        shop_product = line.product.get_shop_instance(shop)
        supplier = shop_product.suppliers.first()
        stock_status = supplier.get_stock_status(line.product.pk) if supplier else None
        base_data.update({
            "type": "product",
            "product": {
                "id": line.product.pk,
                "text": line.product.name
            },
            "step": shop_product.purchase_multiple,
            "logicalCount": stock_status.logical_count if stock_status else 0,
            "physicalCount": stock_status.physical_count if stock_status else 0,
            "salesDecimals": line.product.sales_unit.decimals if line.product.sales_unit else 0,
            "salesUnit": line.product.sales_unit.short_name if line.product.sales_unit else ""
        })
    return base_data


def get_price_info(shop, customer, product, quantity):
    """
    Get price info of given product for given context parameters.

    :type shop: shuup.core.models.Shop
    :type customer: shuup.core.models.Contact
    :type product: shuup.core.models.Product
    :type quantity: numbers.Number
    """
    pricing_mod = get_pricing_module()
    pricing_ctx = pricing_mod.get_context_from_data(
        shop=shop,
        customer=(customer or AnonymousContact()),
    )
    return product.get_price_info(pricing_ctx, quantity=quantity)


class OrderEditView(CreateOrUpdateView):
    model = Order
    template_name = "shuup/admin/orders/create.jinja"
    context_object_name = "order"
    title = _("Create Order")
    fields = []

    def get_context_data(self, **kwargs):
        context = super(OrderEditView, self).get_context_data(**kwargs)
        context["config"] = self.get_config()
        return context

    def get_toolbar(self):
        return Toolbar([])

    def get_config(self):
        order = self.object
        shops = [encode_shop(shop) for shop in Shop.objects.filter(status=ShopStatus.ENABLED)]
        customer_id = self.request.GET.get("contact_id")
        shipping_methods = ShippingMethod.objects.enabled()
        payment_methods = PaymentMethod.objects.enabled()
        return {
            "shops": shops,
            "countries": [{"id": code, "name": name} for code, name in list(countries)],
            "shippingMethods": [encode_method(sm) for sm in shipping_methods],
            "paymentMethods": [encode_method(pm) for pm in payment_methods],
            "orderId": order.pk,
            "orderData": self.get_initial_order_data(),
            "customerData": self.get_customer_data(customer_id) if customer_id else None
        }

    def get_initial_order_data(self):
        order = self.object
        if not order.pk:
            return {}
        return {
            "shop": encode_shop(order.shop),
            "lines": [
                get_line_data_for_edit(order.shop, line) for line in order.lines.filter(
                    type__in=[OrderLineType.PRODUCT, OrderLineType.OTHER], parent_line_id=None
                )
            ],
            "shippingMethodId": (encode_method(order.shipping_method) if order.shipping_method else None),
            "paymentMethodId": (encode_method(order.payment_method) if order.payment_method else None),
            "customer": {
                "id": order.customer.id,
                "name": order.customer.name,
                "isCompany": bool(isinstance(order.customer, CompanyContact)),
                "billingAddress": encode_address(order.billing_address, order.tax_number),
                "shippingAddress": encode_address(order.shipping_address, order.tax_number)
            }
        }

    def get_customer_data(self, customer_id):
        customer = Contact.objects.filter(pk=customer_id).first()
        if not customer:
            return JsonResponse(
                {"success": False, "errorMessage": _("Contact %s does not exist.") % customer_id}, status=400
            )
        tax_number = getattr(customer, "tax_number", "")
        return {
            "id": customer.id,
            "name": customer.name,
            "isCompany": bool(isinstance(customer, CompanyContact)),
            "billingAddress": encode_address(customer.default_billing_address, tax_number),
            "shippingAddress": encode_address(customer.default_shipping_address, tax_number)
        }

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("command"):
            return self.dispatch_command(request)
        return super(OrderEditView, self).dispatch(request, *args, **kwargs)

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
        stock_status = supplier.get_stock_status(product.pk) if supplier else None
        return {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "quantity": quantity,
            "logicalCount": stock_status.logical_count if stock_status else 0,
            "physicalCount": stock_status.physical_count if stock_status else 0,
            "salesDecimals": product.sales_unit.decimals if product.sales_unit else 0,
            "salesUnit": product.sales_unit.short_name if product.sales_unit else "",
            "purchaseMultiple": shop_product.purchase_multiple,
            "taxClass": {
                "id": product.tax_class.id,
                "name": force_text(product.tax_class),
            },
            "baseUnitPrice": {
                "value": price_info.base_unit_price.value,
                "includesTax": price_info.base_unit_price.includes_tax
            },
            "unitPrice": {
                "value": price_info.discounted_unit_price.value,
                "includesTax": price_info.base_unit_price.includes_tax
            },
            "product": {
                "text": product.name,
                "id": product.id,
                "url": get_model_url(product)
            }
        }

    def handle_customer_data(self, request):
        customer_id = request.GET["id"]
        return self.get_customer_data(customer_id)

    def handle_customer_details(self, request):
        customer_id = request.GET["id"]
        customer = Contact.objects.get(pk=customer_id)
        companies = []
        if isinstance(customer, PersonContact):
            companies = sorted(customer.company_memberships.all(), key=(lambda x: force_text(x)))
        recent_orders = customer.customer_orders.order_by('-id')[:10]

        order_summary = []
        for dt in customer.customer_orders.datetimes('order_date', 'year'):
            summary = customer.customer_orders.filter(order_date__year=dt.year).aggregate(
                total=Sum('taxful_total_price_value')
            )
            order_summary.append({
                'year': dt.year,
                'total': format_currency(
                    summary['total'], currency=recent_orders[0].currency, locale=get_current_babel_locale()
                )
            })

        return {
            "customer_info": {
                "name": customer.full_name,
                "phone_no": customer.phone,
                "email": customer.email,
                "companies": [force_text(company) for company in companies] if len(companies) else None,
                "groups": [force_text(group) for group in customer.groups.all()],
                "merchant_notes": customer.merchant_notes
            },
            "order_summary": order_summary,
            "recent_orders": [
                {
                    "order_date": get_locally_formatted_datetime(order.order_date),
                    "total": format_money(order.taxful_total_price),
                    "status": order.get_status_display(),
                    "payment_status": force_text(order.payment_status.label),
                    "shipment_status": force_text(order.shipping_status.label)
                } for order in recent_orders
            ]
        }

    @transaction.atomic
    def _handle_source_data(self, request):
        self.object = self.get_object()
        state = json.loads(request.body.decode("utf-8"))["state"]
        source = create_source_from_state(
            state,
            creator=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
            order_to_update=self.object if self.object.pk else None
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
    def _handle_finalize(self, request):
        state = json.loads(request.body.decode("utf-8"))["state"]
        self.object = self.get_object()
        if self.object.pk:  # Edit
            order = update_order_from_state(
                state,
                self.object,
                modified_by=request.user
            )
            assert self.object.pk == order.pk
            messages.success(request, _("Order %(identifier)s updated.") % vars(order))
        else:  # Create
            order = create_order_from_state(
                state,
                creator=request.user,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, _("Order %(identifier)s created.") % vars(order))
        return JsonResponse({
            "success": True,
            "orderIdentifier": order.identifier,
            "url": reverse("shuup_admin:order.detail", kwargs={"pk": order.pk})
        })

    def handle_source_data(self, request):
        return _handle_or_return_error(self._handle_source_data, request, _("Could not proceed with order:"))

    def handle_finalize(self, request):
        return _handle_or_return_error(self._handle_finalize, request, _("Could not finalize order:"))


def _handle_or_return_error(func, request, error_message):
    try:
        return func(request)
    except Exception as exc:
        if isinstance(exc, ValidationError):
            error_message += "\n" + "\n".join(force_text(err) for err in exc.messages)
        else:
            error_message += " {}".format(exc)
        return JsonResponse({"success": False, "errorMessage": error_message}, status=400)
