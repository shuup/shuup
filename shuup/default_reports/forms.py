# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.core.models import Carrier, Contact, ShippingMethod, Tax, TaxClass
from shuup.reports.forms import BaseReportForm


class OrderReportForm(BaseReportForm):

    def __init__(self, *args, **kwargs):
        super(OrderReportForm, self).__init__(*args, **kwargs)

        customer_field = Select2MultipleField(label=_("Customer"),
                                              model=Contact,
                                              required=False,
                                              help_text=_("Filter report results by customer."))
        customers = self.initial_contacts("customer")
        if customers:
            customer_field.initial = customers
            customer_field.widget.choices = [(obj.pk, obj.name) for obj in customers]
        orderer_field = Select2MultipleField(
            label=_("Orderer"), model=Contact, required=False, help_text=_(
                "Filter report results by the person that made the order."
            )
        )
        orderers = self.initial_contacts("orderer")
        if orderers:
            orderer_field.initial = orderers
            orderer_field.widget.choices = [(obj.pk, obj.name) for obj in orderers]
        self.fields["customer"] = customer_field
        self.fields["orderer"] = orderer_field

    def initial_contacts(self, key):
        if self.data and key in self.data:
            return Contact.objects.filter(pk__in=self.data.getlist(key))
        return []


class ProductTotalSalesReportForm(OrderReportForm):
    SORT_ORDER_CHOICES = (
        ("quantity", _("Quantity")),
        ("taxless_total", _("Taxless Total")),
        ("taxful_total", _("Taxful Total")),
    )

    order_by = forms.ChoiceField(label=_("Sort order"),
                                 initial="quantity",
                                 required=True,
                                 choices=SORT_ORDER_CHOICES)


class NewCustomersReportForm(BaseReportForm):
    GROUP_BY_CHOICES = (
        ("%Y", _("Year")),
        ("%Y-%m", _("Year/Month")),
        ("%Y-%m-%d", _("Year/Month/Day")),
    )

    group_by = forms.ChoiceField(label=_("Group by"),
                                 initial=GROUP_BY_CHOICES[1],
                                 required=True,
                                 choices=GROUP_BY_CHOICES)


class CustomerSalesReportForm(OrderReportForm):
    SORT_ORDER_CHOICES = (
        ("order_count", _("Order Count")),
        ("average_sales", _("Average Sales")),
        ("taxless_total", _("Taxless Total")),
        ("taxful_total", _("Taxful Total")),
    )
    order_by = forms.ChoiceField(label=_("Sort order"),
                                 initial="order_count",
                                 required=True,
                                 choices=SORT_ORDER_CHOICES)


class TaxesReportForm(OrderReportForm):
    tax = Select2MultipleField(label=_("Tax"),
                               model=Tax,
                               required=False,
                               help_text=_("Filter report results by tax."))

    tax_class = Select2MultipleField(label=_("Tax Class"),
                                     model=TaxClass,
                                     required=False,
                                     help_text=_("Filter report results by tax class."))

    def __init__(self, *args, **kwargs):
        super(TaxesReportForm, self).__init__(*args, **kwargs)

        if self.data and "tax" in self.data:
            taxes = Tax.objects.filter(pk__in=self.data.getlist("tax"))
            self.fields["tax"].initial = taxes.first()
            self.fields["tax"].widget.choices = [(obj.pk, obj.name) for obj in taxes]

        if self.data and "tax_class" in self.data:
            tax_classes = TaxClass.objects.filter(pk__in=self.data.getlist("tax_class"))
            self.fields["tax_class"].initial = tax_classes
            self.fields["tax_class"].widget.choices = [(obj.pk, obj.name) for obj in tax_classes]


class ShippingReportForm(OrderReportForm):
    shipping_method = Select2MultipleField(label=_("Shipping Method"),
                                           model=ShippingMethod,
                                           required=False,
                                           help_text=_("Filter report results by shipping method."))

    carrier = Select2MultipleField(label=_("Carrier"),
                                   model=Carrier,
                                   required=False,
                                   help_text=_("Filter report results by carrier."))

    def __init__(self, *args, **kwargs):
        super(ShippingReportForm, self).__init__(*args, **kwargs)

        if self.data and "shipping_method" in self.data:
            shipping_method = ShippingMethod.objects.filter(pk__in=self.data.getlist("shipping_method"))
            self.fields["shipping_method"].initial = shipping_method.first()
            self.fields["shipping_method"].widget.choices = [(obj.pk, obj.name) for obj in shipping_method]

        if self.data and "carrier" in self.data:
            carrier = Carrier.objects.filter(pk__in=self.data.getlist("carrier"))
            self.fields["carrier"].initial = carrier
            self.fields["carrier"].widget.choices = [(obj.pk, obj.name) for obj in carrier]
