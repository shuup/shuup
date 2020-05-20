# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView

from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import Order, Shop
from shuup.utils.analog import LogEntryKind
from shuup.utils.form_group import FormGroup
from shuup.utils.importing import cached_load
from shuup.utils.models import get_data_dict

ADDRESS_EDITED_LOG_IDENTIFIER = "order-address-edited"


class OrderAddressEditView(UpdateView):
    model = Order
    context_object_name = "order"
    template_name = "shuup/admin/orders/_address_edit.jinja"

    def get_queryset(self):
        shop_ids = Shop.objects.get_for_user(self.request.user).values_list("id", flat=True)
        return Order.objects.exclude(deleted=True).filter(shop_id__in=shop_ids)

    def get_form(self, form_class=None):
        order = self.get_object()
        form_group = FormGroup(**self.get_form_kwargs())
        address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")
        form_group.add_form_def(
            "billing_address",
            address_form_class,
            kwargs={"initial": get_data_dict(order.billing_address) if order.billing_address else {}})
        form_group.add_form_def(
            "shipping_address",
            address_form_class,
            kwargs={"initial": get_data_dict(order.shipping_address) if order.shipping_address else {}})
        return form_group

    def form_valid(self, form):
        order = self.get_object()
        for key, field_title in [
                ("billing_address", _("Billing Address")), ("shipping_address", _("Shipping Address"))]:
            if not form[key].has_changed():
                continue
            new_mutable_address = form[key].save()
            new_immutable_address = new_mutable_address.to_immutable()
            new_immutable_address.save()
            old_address = getattr(order, key)
            setattr(order, key, new_immutable_address)
            new_mutable_address.delete()
            order.save(update_fields=[key])
            log_entry_message = _(
                "%(field)s updated from: %(old_address)s") % {"field": field_title, "old_address": old_address}
            order.add_log_entry(
                log_entry_message[:256],
                identifier=ADDRESS_EDITED_LOG_IDENTIFIER,
                kind=LogEntryKind.EDIT
            )
            messages.success(self.request, _("%(field)s were saved.") % {"field": field_title})

        return HttpResponseRedirect(get_model_url(order))

    def get_form_kwargs(self):
        kwargs = super(OrderAddressEditView, self).get_form_kwargs()
        kwargs.pop("instance")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrderAddressEditView, self).get_context_data(**kwargs)
        context["title"] = _("Save -- %s") % context["order"]
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-check-circle",
                form_id="edit-addresses",
                text=_("Save"),
                extra_css_class="btn-primary",
            ),
        ], view=self)
        return context
