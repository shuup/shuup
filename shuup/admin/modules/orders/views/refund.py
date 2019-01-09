# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
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
    InvalidRefundAmountException, NoRefundToCreateException,
    RefundExceedsAmountException
)
from shuup.core.models import Order, OrderLineType
from shuup.utils.money import Money


class RefundForm(forms.Form):
    line_number = forms.ChoiceField(label=_("Line"), required=False, help_text=_(
            "The line to refund. "
            "To refund an amount not associated with any line, select 'Refund arbitrary amount'."
        )
    )
    quantity = forms.DecimalField(required=False, min_value=0, initial=0, label=_("Quantity"), help_text=_(
            "The number of units to refund."
        )
    )
    text = forms.CharField(max_length=255, label=_("Line Text/Comment"), required=False, help_text=_(
            "The text describing the nature of the refund and/or the reason for the refund."
        )
    )
    amount = forms.DecimalField(
        required=False, initial=0, label=_("Amount"), help_text=_("The amount including tax to refund."))
    restock_products = forms.BooleanField(required=False, initial=True, label=_("Restock products"), help_text=_(
            "If checked, the quantity is adding back into the sellable product inventory."
        )
    )

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
        ], view=self)

        # Setting the line_numbers choices dynamically creates issues with the blank formset,
        # So adding that to the context to be rendered manually
        context["line_number_choices"] = self._get_line_number_choices()
        context["json_line_data"] = [self._get_line_data(self.object, line) for line in self.object.lines.all()]
        return context

    def _get_line_data(self, order, line):
        shop = order.shop
        total_price = line.taxful_price.value if shop.prices_include_tax else line.taxless_price.value
        base_data = {
            "id": line.id,
            "type": "other" if line.quantity else "text",
            "text": line.text,
            "quantity": line.quantity - line.refunded_quantity,
            "sku": line.sku,
            "baseUnitPrice": line.base_unit_price.value,
            "unitPrice": total_price / line.quantity if line.quantity else 0,
            "unitPriceIncludesTax": shop.prices_include_tax,
            "amount": line.max_refundable_amount.value,
            "errors": "",
            "step": ""
        }
        if line.product:
            shop_product = line.product.get_shop_instance(shop)
            supplier = line.supplier
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
                "salesUnit": line.product.sales_unit.symbol if line.product.sales_unit else ""
            })
        return base_data

    def get_form_kwargs(self):
        kwargs = super(OrderCreateRefundView, self).get_form_kwargs()
        kwargs.pop("instance")
        return kwargs

    def _get_line_text(self, line):
        text = "line %s: %s" % (line.ordering + 1, line.text)
        if line.sku:
            text += " (SKU %s)" % (line.sku)
        return text

    def _get_line_number_choices(self):
        line_number_choices = [("", "---")]
        if self.object.get_total_unrefunded_amount().value > 0:
            line_number_choices += [("amount", _("Refund arbitrary amount"))]
        return line_number_choices + [
            (line.ordering, self._get_line_text(line)) for line in self.object.lines.all()
            if (line.type == OrderLineType.PRODUCT and line.max_refundable_quantity > 0) or
            (line.type != OrderLineType.PRODUCT and
             line.max_refundable_amount.value > 0 and
             line.max_refundable_quantity > 0) and
            line.type != OrderLineType.REFUND
        ]

    def get_form(self, form_class=None):
        formset = super(OrderCreateRefundView, self).get_form(form_class)

        # Line orderings are zero-indexed, but shouldn't display that way
        choices = self._get_line_number_choices()
        for form in formset.forms:
            form.fields["line_number"].choices = choices
        formset.empty_form.fields["line_number"].choices = choices

        return formset

    def _get_refund_line_info(self, order, data):
        refund_line_info = {}
        amount_value = data.get("amount", 0) or 0
        line_number = data.get("line_number")
        quantity = data.get("quantity", 0) or 1
        restock_products = data.get("restock_products")

        if line_number != "amount":
            line = order.lines.filter(ordering=line_number).first()

            if not line:
                return None
            refund_line_info["line"] = line
            refund_line_info["quantity"] = quantity
            refund_line_info["restock_products"] = bool(restock_products)
        else:
            refund_line_info["line"] = "amount"
            refund_line_info["text"] = data.get("text")
            refund_line_info["quantity"] = 1
        refund_line_info["amount"] = Money(amount_value, order.currency)
        return refund_line_info

    def form_valid(self, form):
        order = self.object
        refund_lines = []

        for refund in form.cleaned_data:
            line = self._get_refund_line_info(order, refund)
            if line:
                refund_lines.append(line)

        try:
            order.create_refund(refund_lines, created_by=self.request.user)
        except RefundExceedsAmountException:
            messages.error(self.request, _("Refund amount exceeds order amount."))
            return self.form_invalid(form)
        except InvalidRefundAmountException:
            messages.error(self.request, _("Refund amounts should match sign on parent line."))
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
        ], view=self)
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
