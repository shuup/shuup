# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from shuup.admin.toolbar import PostActionButton, Toolbar, URLActionButton
from shuup.admin.utils.urls import get_model_url
from shuup.core.excs import (
    NoRefundToCreateException, RefundExceedsAmountException
)
from shuup.core.models import Order
from shuup.utils.money import Money


class RefundForm(forms.Form):
    line_number = forms.ChoiceField(label=_("Line number"), required=False)
    quantity = forms.DecimalField(required=False, min_value=0, initial=0, label=_("Quantity"))
    amount = forms.DecimalField(required=False, min_value=0, initial=0, label=_("Amount"))
    restock_products = forms.BooleanField(required=False, initial=True, label=_("Restock products"))

    def clean_line_number(self):
        line_number = self.cleaned_data["line_number"]
        return line_number if line_number != "" else None

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        return quantity if quantity != 0 else None

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        return amount if amount != 0 else None


class OrderCreateRefundView(UpdateView):
    model = Order
    template_name = "shuup/admin/orders/create_refund.jinja"
    context_object_name = "order"
    form_class = forms.formset_factory(RefundForm, extra=1)

    def get_context_data(self, **kwargs):
        context = super(OrderCreateRefundView, self).get_context_data(**kwargs)
        context["title"] = _("Create Refund -- %s") % context["order"]
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-check-circle",
                form_id="create_refund",
                text=_("Create Refund"),
                extra_css_class="btn-success",
            ),
            URLActionButton(
                url=reverse("shuup_admin:order.create-full-refund", kwargs={"pk": self.object.pk}),
                icon="fa fa-dollar",
                text=_("Refund Entire Order"),
                extra_css_class="btn-info",
                disable_reason=_("This order already has existing refunds") if self.object.has_refunds() else None
            ),
        ])

        # Setting the line_numbers choices dynamically creates issues with the blank formset,
        # So adding that to the context to be rendered manually
        context["line_number_choices"] = self._get_line_number_choices()
        context["json_line_data"] = [self._get_line_data(self.object.shop, line) for line in self.object.lines.all()]

        return context

    def _get_line_data(self, shop, line):
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

    def get_form_kwargs(self):
        kwargs = super(OrderCreateRefundView, self).get_form_kwargs()
        kwargs.pop("instance")
        return kwargs

    def _get_refundable_line_numbers(self):
        return [line.ordering for line in self.object.lines.all() if line.max_refundable_amount.value > 0]

    def _get_line_number_choices(self):
        return [("", "---")] + [((i), (i+1)) for i in self._get_refundable_line_numbers()]

    def get_form(self, form_class):
        formset = super(OrderCreateRefundView, self).get_form(form_class)

        # Line orderings are zero-indexed, but shouldn't display that way
        choices = self._get_line_number_choices()
        for form in formset.forms:
            form.fields["line_number"].choices = choices
        formset.empty_form.fields["line_number"].choices = choices

        return formset

    def _get_refund_line_info(self, order, data):
        refund_line_info = {}
        total_amount = Money(0, order.currency)
        amount_value = data.get("amount", 0)
        line_number = data.get("line_number")
        quantity = data.get("quantity", 0)
        restock_products = data.get("restock_products")

        if amount_value:
            amount = Money(amount_value, order.currency)
            refund_line_info["amount"] = amount
            total_amount += amount

        if line_number:
            line = order.lines.get(ordering=line_number)
            refund_line_info["line"] = line

            if data.get("quantity", None):
                unit_price = line.base_unit_price.amount
                quantity = data["quantity"]
                calculated_refund_amount = unit_price * quantity

                refund_line_info["quantity"] = quantity
                total_amount += calculated_refund_amount
                # Add taxes to refund or somehow otherwise include it

            # Check to make sure total amount isn't more than line total
            if total_amount > line.max_refundable_amount:
                raise RefundExceedsAmountException

            refund_line_info["restock_products"] = bool(restock_products)

        return refund_line_info if total_amount else {}

    def form_valid(self, form):
        order = self.object
        refund_lines = []

        for refund in form.cleaned_data:
            try:
                line = self._get_refund_line_info(order, refund)
                if line:
                    refund_lines.append(line)
            except RefundExceedsAmountException:
                messages.error(self.request, _("Refund amount exceeds order amount."))
                return self.form_invalid(form)
        if not refund_lines:
            messages.error(self.request, _("Refund amount cannot be 0"))
            return self.form_invalid(form)

        try:
            order.create_refund(refund_lines, created_by=self.request.user)
        except RefundExceedsAmountException:
            messages.error(self.request, _("Refund amount exceeds order amount."))
            return self.form_invalid(form)

        messages.success(self.request, _("Refund created."))
        return HttpResponseRedirect(get_model_url(order))


class FullRefundConfirmationForm(forms.Form):
    restock_products = forms.BooleanField(required=False, initial=True, label=_("Restock products"))


class OrderCreateFullRefundView(UpdateView):
    model = Order
    template_name = "shuup/admin/orders/create_full_refund.jinja"
    context_object_name = "order"
    form_class = FullRefundConfirmationForm

    def get_context_data(self, **kwargs):
        context = super(OrderCreateFullRefundView, self).get_context_data(**kwargs)
        context["title"] = _("Create Full Refund -- %s") % context["order"]
        context["toolbar"] = Toolbar([
            URLActionButton(
                url=reverse("shuup_admin:order.create-refund", kwargs={"pk": self.object.pk}),
                icon="fa fa-check-circle",
                text=_("Cancel"),
                extra_css_class="btn-danger",
            ),
        ])
        return context

    def get_form_kwargs(self):
        kwargs = super(OrderCreateFullRefundView, self).get_form_kwargs()
        kwargs.pop("instance")
        return kwargs

    def form_valid(self, form):
        order = self.object
        restock_products = bool(form.cleaned_data.get("restock_products"))

        try:
            order.create_full_refund(restock_products)
        except NoRefundToCreateException:
            messages.error(self.request, _("Could not create full refund."))
            return self.form_invalid(form)

        messages.success(self.request, _("Full refund created."))
        return HttpResponseRedirect(get_model_url(order))
