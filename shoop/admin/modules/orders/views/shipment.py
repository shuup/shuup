# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from shoop.admin.toolbar import PostActionButton, Toolbar
from shoop.admin.utils.forms import add_form_errors_as_messages
from shoop.admin.utils.urls import get_model_url
from shoop.core.excs import NoProductsToShipException
from shoop.core.models import Order, Product, Supplier


class OrderCreateShipmentView(UpdateView):
    model = Order
    template_name = "shoop/admin/orders/create_shipment.jinja"
    context_object_name = "order"
    form_class = forms.Form  # Augmented manually

    def get_context_data(self, **kwargs):
        context = super(OrderCreateShipmentView, self).get_context_data(**kwargs)
        context["title"] = _("Create Shipment -- %s") % context["order"]
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-check-circle",
                form_id="create_shipment",
                text=_("Create Shipment"),
                extra_css_class="btn-success",
            ),
        ])
        return context

    def get_form_kwargs(self):
        kwargs = super(OrderCreateShipmentView, self).get_form_kwargs()
        kwargs.pop("instance")
        return kwargs

    def get_form(self, form_class):
        form = super(OrderCreateShipmentView, self).get_form(form_class)
        order = self.object
        form.fields["supplier"] = forms.ModelChoiceField(
            queryset=Supplier.objects.all(),
            initial=Supplier.objects.first(),
            label=_("Supplier")
        )
        form.product_summary = order.get_product_summary()
        form.product_names = dict(
            (product_id, text)
            for (product_id, text)
            in order.lines.exclude(product=None).values_list("product_id", "text")
        )
        for product_id, info in sorted(six.iteritems(form.product_summary)):
            product_name = form.product_names.get(product_id, "Product %s" % product_id)
            attrs = {"data-max": info["unshipped"], "class": "form-control text-right", }
            if info["unshipped"] == 0:
                attrs["disabled"] = "disabled"
            field = forms.DecimalField(
                min_value=0,
                max_value=info["unshipped"],
                initial=0,
                label=product_name,
                widget=forms.TextInput(attrs=attrs)
            )
            form.fields["q_%s" % product_id] = field

        return form

    def form_invalid(self, form):
        add_form_errors_as_messages(self.request, form)
        return super(OrderCreateShipmentView, self).form_invalid(form)

    def form_valid(self, form):
        product_ids_to_quantities = dict(
            (int(key.replace("q_", "")), value)
            for (key, value)
            in six.iteritems(form.cleaned_data)
            if key.startswith("q_") and value > 0
        )
        order = self.object
        product_map = Product.objects.in_bulk(set(product_ids_to_quantities.keys()))
        products_to_quantities = dict(
            (product_map[product_id], quantity)
            for (product_id, quantity)
            in six.iteritems(product_ids_to_quantities)
        )
        try:
            shipment = order.create_shipment(
                supplier=form.cleaned_data["supplier"],
                product_quantities=products_to_quantities
            )
        except NoProductsToShipException:
            messages.error(self.request, _("No products to ship."))
            return self.form_invalid(form)
        else:
            messages.success(self.request, _("Shipment %s created.") % shipment.id)
            return HttpResponseRedirect(get_model_url(order))
