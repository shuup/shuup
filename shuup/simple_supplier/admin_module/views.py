# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Product, Supplier
from shuup.core.utils import context_cache
from shuup.simple_supplier.forms import AlertLimitForm, StockAdjustmentForm
from shuup.simple_supplier.models import StockCount
from shuup.simple_supplier.utils import (
    get_stock_adjustment_div, get_stock_information_div_id,
    get_stock_information_html
)


class StocksListView(PicotableListView):
    template_name = "shuup/simple_supplier/admin/base_picotable.jinja"
    model = Product
    default_columns = [
        Column(
            "sku", _("SKU"), sort_field="product__sku", display="product__sku", linked=True,
            filter_config=TextFilter(filter_field="product__sku", placeholder=_("Filter by SKU..."))
        ),
        Column(
            "name", _("Name"), sort_field="product__translations__name", display="product__name", linked=True,
            filter_config=TextFilter(filter_field="product__translations__name", placeholder=_("Filter by name..."))
        ),
        Column(
            "supplier", _("Supplier"), display="supplier", linked=False,
            filter_config=ChoicesFilter(Supplier.objects.enabled().filter(module_identifier="simple_supplier"))
        ),
        Column(
            "stock_information", _("Stock information"), display="get_stock_information",
            linked=False, sortable=False, raw=True
        ),
        Column(
            "adjust_stock", _("Adjust stock"), display="get_stock_adjustment_form",
            sortable=False, linked=False, raw=True
        )
    ]

    def __init__(self):
        super(StocksListView, self).__init__()
        self.columns = self.default_columns

    def get_object_abstract(self, instance, item):
        item.update({"_linked_in_mobile": False, "_url": ""})
        return [
            {"text": item.get("name"), "class": "header"},
            {"title": "", "text": item.get("sku")},
            {"title": "", "text": " ", "raw": item.get("stock_information")},
            {"title": "", "text": " ", "raw": item.get("adjust_stock")},
        ]

    def get_queryset(self):
        return StockCount.objects.filter(
            supplier__module_identifier="simple_supplier",
            supplier__enabled=True,
            supplier__stock_managed=True,
            product__deleted=False
        ).order_by("product__id")

    def get_context_data(self, **kwargs):
        context = super(PicotableListView, self).get_context_data(**kwargs)
        context["toolbar"] = None
        context["title"] = _("Stock management")
        return context

    def get_stock_information(self, instance):
        return get_stock_information_html(instance.supplier, instance.product)

    def get_stock_adjustment_form(self, instance):
        return get_stock_adjustment_div(self.request, instance.supplier, instance.product)


def get_adjustment_success_message(stock_adjustment):
    arguments = {
        "delta": stock_adjustment.delta,
        "unit_symbol": stock_adjustment.product.sales_unit.symbol,
        "product_name": stock_adjustment.product.name,
        "supplier_name": stock_adjustment.supplier.name
    }
    if stock_adjustment.delta > 0:
        return _(
            "Success! Added %(delta)s `%(unit_symbol)s` for product `%(product_name)s` stock (%(supplier_name)s)."
        ) % arguments
    else:
        return _(
            "Success! Removed %(delta)s `%(unit_symbol)s` from product `%(product_name)s` stock (%(supplier_name)s)."
        ) % arguments


def _get_success_message(request, supplier, product, message):
    return {
        "stockInformationDiv": "#%s" % get_stock_information_div_id(supplier, product),
        "updatedStockInformation": get_stock_information_html(supplier, product),
        "updatedStockManagement": get_stock_adjustment_div(request, supplier, product),
        "message": message
    }


def _process_stock_adjustment(form, request, supplier_id, product_id):
    data = form.cleaned_data
    supplier = Supplier.objects.get(id=supplier_id)
    stock_adjustment = supplier.module.adjust_stock(
        product_id,
        delta=data.get("delta"),
        purchase_price=data.get("purchase_price"),
        created_by=request.user
    )
    success_message = _get_success_message(
        request,
        stock_adjustment.supplier,
        stock_adjustment.product,
        get_adjustment_success_message(stock_adjustment)
    )
    return JsonResponse(success_message, status=200)


def process_stock_adjustment(request, supplier_id, product_id):
    return _process_and_catch_errors(
        _process_stock_adjustment, StockAdjustmentForm, request, supplier_id, product_id)


def _process_alert_limit(form, request, supplier_id, product_id):
    supplier = Supplier.objects.get(id=supplier_id)
    product = Product.objects.get(id=product_id)
    sc = StockCount.objects.get(supplier=supplier, product=product)
    data = form.cleaned_data
    sc.alert_limit = data.get("alert_limit")
    sc.save()

    supplier = Supplier.objects.get(id=supplier_id)

    success_message = _get_success_message(
        request,
        supplier,
        product,
        _("Alert limit for product `%(product_name)s` set to `%(value)s`.") % {
            "product_name": product.name,
            "value": sc.alert_limit
        }
    )
    return JsonResponse(success_message, status=200)


def process_alert_limit(request, supplier_id, product_id):
    return _process_and_catch_errors(
        _process_alert_limit, AlertLimitForm, request, supplier_id, product_id)


def _process_and_catch_errors(process, form_class, request, supplier_id, product_id):
    try:
        if request.method != "POST":
            raise Exception(_("Non-POST request methods are forbidden."))
        form = form_class(request.POST)
        if form.is_valid():
            return process(form, request, supplier_id, product_id)

        error_message = ugettext("Please check submitted values and try again.")
        return JsonResponse({"message": error_message}, status=400)
    except Exception as exc:
        error_message = ugettext(
            "Please check submitted values and try again (%(error)s).") % {"error":  exc}
        return JsonResponse({"message": error_message}, status=400)


def process_stock_managed(request, supplier_id, product_id):
    if request.method != "POST":
        raise Exception(_("Non-POST request methods are forbidden."))

    stock_managed = bool(request.POST.get("stock_managed") == "True")
    supplier = Supplier.objects.get(id=supplier_id)
    product = Product.objects.get(id=product_id)
    stock_count = StockCount.objects.get_or_create(supplier=supplier, product=product)[0]
    stock_count.stock_managed = stock_managed
    stock_count.save(update_fields=["stock_managed"])

    for shop in supplier.shops.all():
        context_cache.bump_cache_for_product(product, shop=shop)

    if stock_managed:
        msg = _("Stock management is now enabled for {product}.").format(product=product)
    else:
        msg = _("Stock management is now disabled for {product}.").format(product=product)

    success_message = _get_success_message(request, supplier, product, msg)
    return JsonResponse(success_message, status=200)
