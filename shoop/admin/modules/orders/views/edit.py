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

from babel.numbers import format_currency, format_decimal
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.http.response import HttpResponse, JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django_countries import countries

from shoop.admin.base import MenuEntry
from shoop.admin.modules.orders.json_order_creator import (
    JsonPurchaseOrderCreator, JsonSalesOrderCreator
)
from shoop.admin.toolbar import Toolbar
from shoop.admin.utils.urls import get_model_url
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import (
    AnonymousContact, CompanyContact, Contact, Manufacturer, Order,
    OrderLineType, PaymentMethod, PersonContact, Product, PurchaseOrder,
    ShippingMethod, Shop, ShopStatus
)
from shoop.core.pricing import get_pricing_module
from shoop.utils.i18n import (
    format_money, format_percent, get_current_babel_locale,
    get_locally_formatted_datetime
)


def get_order_creator_for_type(type):
    if type == "sales":
        return JsonSalesOrderCreator()
    else:
        return JsonPurchaseOrderCreator()


def create_order_from_state(state, **kwargs):
    joc = get_order_creator_for_type(state["order"]["type"])
    order = joc.create_order_from_state(state, **kwargs)
    if not order:
        raise ValidationError(list(joc.errors))
    return order


def update_order_from_state(state, order_to_update, **kwargs):
    joc = get_order_creator_for_type(state["order"]["type"])
    order = joc.update_order_from_state(state, order_to_update, **kwargs)
    if not order:
        raise ValidationError(list(joc.errors))
    return order


def create_source_from_state(state, **kwargs):
    joc = get_order_creator_for_type(state["order"]["type"])
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


def encode_manufacturer_data(manufacturer):
    return {
        "id": manufacturer.id,
        "name": manufacturer.name
    }


def encode_customer_data(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "isCompany": bool(isinstance(customer, CompanyContact)),
        "billingAddress": encode_address(customer.default_billing_address),
        "shippingAddress": encode_address(customer.default_shipping_address)
    }


def encode_order_data_for_edit(order):
    return {
        "shop": encode_shop(order.shop),
        "lines": [
            encode_line_data_for_edit(order.shop, line) for line in order.lines.filter(
                type__in=[OrderLineType.PRODUCT, OrderLineType.OTHER], parent_line_id=None
            )
        ],
        "shippingMethodId": (encode_method(order.shipping_method) if order.shipping_method else None),
        "paymentMethodId": (encode_method(order.payment_method) if order.payment_method else None),
        "customer": {
            "id": order.customer.id,
            "name": order.customer.name,
            "isCompany": bool(isinstance(order.customer, CompanyContact)),
            "billingAddress": encode_address(order.billing_address),
            "shippingAddress": encode_address(order.shipping_address)
        }
    }


def encode_line_data_for_edit(shop, line):
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
    return product.get_price_info(pricing_ctx, quantity=quantity)


def get_product_data(request, for_purchase_order=False):
    product_id = request.GET["id"]
    shop_id = request.GET["shop_id"]
    customer_id = request.GET.get("customer_id")
    quantity = decimal.Decimal(request.GET.get("quantity", 1))
    already_in_lines_qty = decimal.Decimal(request.GET.get("already_in_lines_qty", 0))
    product = Product.objects.filter(pk=product_id).first()
    errors = None
    price_dict = None
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
    # TODO: Allow setting a supplier?
    supplier = shop_product.suppliers.filter().first()
    stock_status = supplier.get_stock_status(product.pk) if supplier else None
    if not for_purchase_order:
        errors = " ".join(
            [str(message.args[0]) for message in shop_product.get_orderability_errors(
                supplier=supplier, quantity=(quantity + already_in_lines_qty), customer=customer, ignore_minimum=True)])
    product_data = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "quantity": quantity,
        "logicalCount": stock_status.logical_count if stock_status else 0,
        "physicalCount": stock_status.physical_count if stock_status else 0,
        "salesDecimals": product.sales_unit.decimals if product.sales_unit else 0,
        "salesUnit": product.sales_unit.short_name if product.sales_unit else "",
        "purchaseMultiple": shop_product.purchase_multiple,
        "errors": errors,
        "taxClass": {
            "id": product.tax_class.id,
            "name": force_text(product.tax_class),
        }
    }

    if for_purchase_order:
        purchase_price = supplier.get_latest_purchase_price(product.id) if supplier else None
        if purchase_price:
            price_dict = {
                "baseUnitPrice": {
                    "value": purchase_price.value,
                    "includesTax": purchase_price.includes_tax
                }
            }
            price_dict["unitPrice"] = price_dict["baseUnitPrice"]

    if not price_dict:
        price_info = get_price_info(shop, customer, product, quantity)
        price_dict = {
            "baseUnitPrice": {
                "value": price_info.base_unit_price.value,
                "includesTax": price_info.base_unit_price.includes_tax
            },
            "unitPrice": {
                "value": price_info.discounted_unit_price.value,
                "includesTax": price_info.base_unit_price.includes_tax
            }
        }
    product_data.update(price_dict)
    return product_data


class BaseOrderEditView(CreateOrUpdateView):
    template_name = "shoop/admin/orders/create.jinja"
    context_object_name = "order"
    title = _("Create Order")
    fields = []

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=self.object._meta.verbose_name_plural.title(),
                url=get_model_url(self.object, kind="list")
            )
        ]

    def get_context_data(self, **kwargs):
        context = super(BaseOrderEditView, self).get_context_data(**kwargs)
        context["config"] = {
            "shops": [encode_shop(shop) for shop in Shop.objects.filter(status=ShopStatus.ENABLED)],
            "orderId": self.object.pk,
            "orderData": encode_order_data_for_edit(self.object) if self.object.pk else {}
        }
        return context

    def get_toolbar(self):
        return Toolbar([])

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("command"):
            return self.dispatch_command(request)
        return super(BaseOrderEditView, self).dispatch(request, *args, **kwargs)

    def dispatch_command(self, request):
        handler = getattr(self, "handle_%s" % request.GET.get("command"), None)
        if not callable(handler):
            return JsonResponse({"error": "unknown command %s" % request.GET.get("command")}, status=400)
        retval = handler(request)
        if not isinstance(retval, HttpResponse):
            retval = JsonResponse(retval)
        return retval

    def handle_product_data(self, request):
        return {}

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
            "url": get_model_url(self.object, kind="list")
        })

    def handle_source_data(self, request):
        return _handle_or_return_error(self._handle_source_data, request, _("Could not proceed with order:"))

    def handle_finalize(self, request):
        return _handle_or_return_error(self._handle_finalize, request, _("Could not finalize order:"))


class OrderEditView(BaseOrderEditView):
    model = Order

    def get_queryset(self):
        return Order.objects.sales_orders()

    def get_context_data(self, **kwargs):
        context = super(OrderEditView, self).get_context_data(**kwargs)
        customer_id = self.request.GET.get("contact_id")
        customer = Contact.objects.filter(pk=customer_id).first()
        shipping_methods = ShippingMethod.objects.enabled()
        payment_methods = PaymentMethod.objects.enabled()
        context["config"].update({
            "orderType": "sales",
            "countries": [{"id": code, "name": name} for code, name in list(countries)],
            "shippingMethods": [encode_method(sm) for sm in shipping_methods],
            "paymentMethods": [encode_method(pm) for pm in payment_methods],
            "customerData": encode_customer_data(customer) if customer else None
        })
        return context

    def handle_customer_data(self, request):
        customer_id = request.GET["id"]
        customer = Contact.objects.filter(pk=customer_id).first()
        if not customer:
            return JsonResponse(
                {"success": False, "errorMessage": _("Contact %s does not exist.") % customer_id}, status=400
            )
        return encode_customer_data(customer)

    def handle_customer_details(self, request):
        customer_id = request.GET["id"]
        customer = Contact.objects.get(pk=customer_id)
        companies = []
        if isinstance(customer, PersonContact):
            companies = sorted(customer.company_memberships.all(), key=(lambda x: force_text(x)))
        customer_sales_orders = customer.customer_orders.filter(purchaseorder__isnull=True)
        recent_orders = customer_sales_orders.order_by('-id')[:10]

        order_summary = []
        for dt in customer_sales_orders.datetimes('order_date', 'year'):
            summary = customer_sales_orders.filter(order_date__year=dt.year).aggregate(
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
                "companies": companies if len(companies) else None,
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

    def handle_product_data(self, request):
        return get_product_data(request)


class PurchaseOrderEditView(BaseOrderEditView):
    model = PurchaseOrder

    def get_context_data(self, **kwargs):
        context = super(PurchaseOrderEditView, self).get_context_data(**kwargs)
        manufacturer_id = self.request.GET.get("manufacturer_id")
        context["config"].update({
            "orderType": "purchase",
            "manufacturers": [encode_manufacturer_data(manufacturer) for manufacturer in Manufacturer.objects.all()],
            "manufacturer": manufacturer_id
        })
        return context

    def handle_product_data(self, request):
        return get_product_data(request, for_purchase_order=True)


def _handle_or_return_error(func, request, error_message):
    try:
        return func(request)
    except Exception as exc:
        if isinstance(exc, ValidationError):
            error_message += "\n" + "\n".join(force_text(err) for err in exc.messages)
        else:
            error_message += " {}".format(exc)
        return JsonResponse({"success": False, "errorMessage": error_message}, status=400)
