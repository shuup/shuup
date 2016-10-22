# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, UpdateView

from shuup.admin.form_modifier import ModifiableFormMixin, ModifiableViewMixin
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.forms import add_form_errors_as_messages
from shuup.admin.utils.urls import get_model_url
from shuup.core.excs import (
    NoProductsToShipException, NoShippingAddressException
)
from shuup.core.models import Order, Product, Shipment, Supplier
from shuup.utils.excs import Problem


class ShipmentForm(ModifiableFormMixin, forms.Form):
    form_modifier_provide_key = "admin_extend_create_shipment_form"

    description = forms.CharField(required=False)
    tracking_code = forms.CharField(required=False)


class OrderCreateShipmentView(ModifiableViewMixin, UpdateView):
    model = Order
    template_name = "shuup/admin/orders/create_shipment.jinja"
    context_object_name = "order"
    form_class = ShipmentForm  # Augmented manually

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

    def get_form(self):
        default_field_keys = set()
        form = super(OrderCreateShipmentView, self).get_form()
        order = self.object
        form.fields["supplier"] = forms.ModelChoiceField(
            queryset=Supplier.objects.all(),
            initial=Supplier.objects.first(),
            label=_("Supplier")
        )
        default_field_keys.add("supplier")
        form.product_summary = order.get_product_summary()
        form.product_names = dict(
            (product_id, text)
            for (product_id, text)
            in order.lines.exclude(product=None).values_list("product_id", "text")
        )
        for product_id, info in sorted(six.iteritems(form.product_summary)):
            product_name = form.product_names.get(product_id, "Product %s" % product_id)
            unshipped_count = info["unshipped"]
            attrs = {"data-max": unshipped_count, "class": "form-control text-right", }
            if unshipped_count == 0:
                attrs["disabled"] = "disabled"
            field = forms.DecimalField(
                required=bool(unshipped_count != 0),
                min_value=0,
                max_value=unshipped_count,
                initial=0,
                label=product_name,
                widget=forms.TextInput(attrs=attrs)
            )
            field_key = "q_%s" % product_id
            form.fields[field_key] = field
            default_field_keys.add(field_key)

        form.default_field_keys = default_field_keys
        return form

    def form_invalid(self, form):
        add_form_errors_as_messages(self.request, form)
        return super(OrderCreateShipmentView, self).form_invalid(form)

    def form_valid(self, form):
        product_ids_to_quantities = dict(
            (int(key.replace("q_", "")), value)
            for (key, value)
            in six.iteritems(form.cleaned_data)
            if key.startswith("q_") and (value > 0 if value else False)
        )
        order = self.object
        product_map = Product.objects.in_bulk(set(product_ids_to_quantities.keys()))
        products_to_quantities = dict(
            (product_map[product_id], quantity)
            for (product_id, quantity)
            in six.iteritems(product_ids_to_quantities)
        )

        unsaved_shipment = Shipment(order=order,
                                    supplier=form.cleaned_data["supplier"],
                                    tracking_code=form.cleaned_data.get("tracking_code"),
                                    description=form.cleaned_data.get("description"),)
        has_extension_errors = self.form_valid_hook(form, unsaved_shipment)

        if has_extension_errors:
            return self.form_invalid(form)

        try:
            shipment = order.create_shipment(
                product_quantities=products_to_quantities,
                shipment=unsaved_shipment
            )
        except Problem as problem:
            messages.error(self.request, problem)
            return self.form_invalid(form)
        except NoProductsToShipException:
            messages.error(self.request, _("No products to ship."))
            return self.form_invalid(form)
        except NoShippingAddressException:
            messages.error(self.request, _("Shipping address is not set."))
        else:
            messages.success(self.request, _("Shipment %s created.") % shipment.id)
            return HttpResponseRedirect(get_model_url(order))


class ShipmentDeleteView(DetailView):
    model = Shipment
    context_object_name = "shipment"

    def get(self, request, *args, **kwargs):
        shipment = self.get_object()
        return HttpResponseRedirect(get_model_url(shipment.order))

    def post(self, request, *args, **kwargs):
        shipment = self.get_object()
        shipment.soft_delete()
        messages.success(request, _("Shipment %s has been deleted.") % shipment.pk)
        return HttpResponseRedirect(get_model_url(shipment.order))
