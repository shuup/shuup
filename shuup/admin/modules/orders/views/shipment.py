# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc

import six
from django import forms
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.forms import add_form_errors_as_messages
from shuup.admin.utils.urls import get_model_url
from shuup.apps.provides import get_provide_objects
from shuup.core.excs import NoProductsToShipException
from shuup.core.models import Order, Product, Shipment, Supplier

FORM_MODIFIER_PROVIDER_KEY = "admin_extend_create_shipment_form"


class ShipmentFormModifier(six.with_metaclass(abc.ABCMeta)):
    def get_extra_fields(self, order):
        """
        Extra fields for shipment creation view.

        :param order: Order linked to form
        :type order: shuup.core.models.Order
        :return: List of extra fields that should be added to form.
        Tuple should contain field name and Django form field.
        :rtype: list[(str,django.forms.Field)]
        """
        pass

    def clean_hook(self, form):
        """
        Extra clean for shipment creation form.

        This hook will be called in `~Django.forms.Form.clean` method of
        the form, after calling parent clean.  Implementor of this hook
        may call `~Django.forms.Form.add_error` to add errors to form or
        modify the ``form.cleaned_data`` dictionary.

        :param form: Form that is currently cleaned
        :type form: ShipmentForm
        :rtype: None
        """
        pass

    def form_valid_hook(self, form, shipment):
        """
        Extra form valid handler for shipment creation view.

        This is called from ``OrderCreateShipmentView`` just
        before the ``Order.create_shipment``

        :param form: Form that is currently handled
        :type form: ShipmentForm
        :param shipment: Unsaved shipment
        :type shipment: shuup.core.models.Shipment
        :rtype: None
        """
        pass


class ShipmentForm(forms.Form):
    def clean(self):
        cleaned_data = super(ShipmentForm, self).clean()
        for extend_class in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
            extend_class().clean_hook(self)
        return cleaned_data


class OrderCreateShipmentView(UpdateView):
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

    def get_form(self, form_class):
        default_field_keys = set()
        form = super(OrderCreateShipmentView, self).get_form(form_class)
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

        for extend_class in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
            for field_key, field in extend_class().get_extra_fields(order) or []:
                form.fields[field_key] = field

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
            if key.startswith("q_") and value > 0
        )
        order = self.object
        product_map = Product.objects.in_bulk(set(product_ids_to_quantities.keys()))
        products_to_quantities = dict(
            (product_map[product_id], quantity)
            for (product_id, quantity)
            in six.iteritems(product_ids_to_quantities)
        )

        unsaved_shipment = Shipment(order=order, supplier=form.cleaned_data["supplier"])
        for extend_class in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
            extend_class().form_valid_hook(form, unsaved_shipment)
        try:
            shipment = order.create_shipment(
                product_quantities=products_to_quantities,
                shipment=unsaved_shipment
            )
        except NoProductsToShipException:
            messages.error(self.request, _("No products to ship."))
            return self.form_invalid(form)
        else:
            messages.success(self.request, _("Shipment %s created.") % shipment.id)
            return HttpResponseRedirect(get_model_url(order))
