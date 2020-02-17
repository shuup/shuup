# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

from django.utils.html import escape
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, MultiFieldTextFilter, RangeFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Shop
from shuup.front.admin_module.carts.form_parts import get_cart_delay_hours
from shuup.front.models import StoredBasket
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class CartListView(PicotableListView):
    model = StoredBasket
    default_columns = [
        Column("created_on", _(u"Created on"), display="format_created_date", filter_config=DateRangeFilter()),
        Column("updated_on", _(u"Last updated on"), display="format_updated_date", filter_config=DateRangeFilter()),
        Column(
            "finished", _("Abandoned"),
            display="format_abandoned_status",
            filter_config=ChoicesFilter([(False, _("yes")), (True, _("no"))])
        ),
        Column("shop", _("Shop"), filter_config=ChoicesFilter("get_shops")),
        Column("product_count", _("Product count"), filter_config=RangeFilter()),
        Column(
            "customer", _(u"Customer"),
            filter_config=MultiFieldTextFilter(filter_fields=("customer__email", "customer__name"))
        ),
        Column(
            "orderer", _(u"Orderer"),
            filter_config=MultiFieldTextFilter(filter_fields=("orderer__email", "orderer__name"))
        ),
        Column(
            "taxful_total_price", _(u"Total"), sort_field="taxful_total_price_value",
            display="format_taxful_total_price", class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value")
        ),
    ]
    toolbar_buttons_provider_key = "cart_list_toolbar_provider"
    mass_actions_provider_key = "cart_list_actions_provider"

    def get_shops(self):
        return Shop.objects.get_for_user(self.request.user)

    def get_queryset(self):
        """
        Ignore potentially active carts, displaying only those not updated for at least 2 hours.
        """
        shop = get_shop(self.request)
        cutoff = now() - datetime.timedelta(hours=get_cart_delay_hours(shop))
        filters = {"updated_on__lt": cutoff, "product_count__gte": 0, "persistent": False, "shop": shop}
        return super(CartListView, self).get_queryset().filter(**filters)

    def format_abandoned_status(self, instance, *args, **kwargs):
        return "yes" if not instance.finished else "no"

    def format_created_date(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.created_on)

    def format_updated_date(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.updated_on)

    def format_taxful_total_price(self, instance, *args, **kwargs):
        if not instance.taxful_total_price:
            return ""
        return escape(format_money(instance.taxful_total_price))

    def get_context_data(self, **kwargs):
        context = super(CartListView, self).get_context_data(**kwargs)
        context["title"] = _("Carts")
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Created on"), "text": item.get("created_on")},
            {"title": _(u"Last updated on"), "text": item.get("updated_on")},
            {"title": _(u"Ordered"), "text": item.get("finished")},
            {"title": _(u"Total"), "text": item.get("taxful_total_price")},
        ]
