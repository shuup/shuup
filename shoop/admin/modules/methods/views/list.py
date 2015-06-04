# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from shoop.admin.toolbar import Toolbar, NewActionButton
from shoop.admin.utils.picotable import Column, PicotableViewMixin, TextFilter, ChoicesFilter
from shoop.core.models.methods import Method, MethodStatus, ShippingMethod, PaymentMethod


class _BaseMethodListView(PicotableViewMixin, ListView):
    action_url_name_prefix = None
    model = Method
    columns = [
        Column("name", _(u"Name"), sort_field="translations__name", filter_config=TextFilter(
            filter_field="name",
            placeholder=_("Filter by name...")
        )),
        Column("status", _(u"Status"), filter_config=ChoicesFilter(choices=MethodStatus.choices)),
    ]

    def get_context_data(self, **kwargs):
        context = super(_BaseMethodListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([NewActionButton("shoop_admin:%s.new" % self.action_url_name_prefix)])
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Status"), "text": item["status"]}
        ]


class ShippingMethodListView(_BaseMethodListView):
    model = ShippingMethod
    action_url_name_prefix = "method.shipping"


class PaymentMethodListView(_BaseMethodListView):
    model = PaymentMethod
    action_url_name_prefix = "method.payment"
