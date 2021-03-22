# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.picotable import (
    ChoicesFilter,
    Column,
    DateRangeFilter,
    MultiFieldTextFilter,
    RangeFilter,
    TextFilter,
)
from shuup.admin.utils.views import PicotableListView
from shuup.front.models import StoredBasket
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class CartListView(PicotableListView):
    model = StoredBasket
    default_columns = [
        Column("key", _("Key"), filter_config=TextFilter(filter_field="key")),
        Column("updated_on", _("Last updated on"), display="format_updated_date", filter_config=DateRangeFilter()),
        Column(
            "finished",
            _("Completed"),
            display="format_finished_status",
            filter_config=ChoicesFilter([(True, _("yes")), (False, _("no"))], filter_field="finished", default=False),
        ),
        Column("shop", _("Shop"), filter_config=TextFilter(filter_field="shop__translations__public_name")),
        Column("supplier", _("Supplier"), filter_config=TextFilter(filter_field="supplier__name")),
        Column(
            "customer",
            _("Customer"),
            filter_config=MultiFieldTextFilter(filter_fields=("customer__email", "customer__name")),
        ),
        Column("product_count", _("Product count"), filter_config=RangeFilter()),
        Column(
            "taxful_total_price",
            _("Total"),
            sort_field="taxful_total_price_value",
            display="format_taxful_total_price",
            class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value"),
        ),
    ]
    toolbar_buttons_provider_key = "cart_list_toolbar_provider"
    mass_actions_provider_key = "cart_list_actions_provider"

    def __init__(self):
        super(CartListView, self).__init__()
        self.columns = self.default_columns

    def get_queryset(self):
        """
        Ignore potentially active carts, displaying only those not updated for at least 2 hours.
        """
        shop = get_shop(self.request)
        filters = {"product_count__gte": 0, "persistent": False, "shop": shop}
        return super(CartListView, self).get_queryset().filter(**filters)

    def format_finished_status(self, instance, *args, **kwargs):
        return "yes" if instance.finished else "no"

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
            {"title": _("Created on"), "text": item.get("created_on")},
            {"title": _("Last updated on"), "text": item.get("updated_on")},
            {"title": _("Ordered"), "text": item.get("finished")},
            {"title": _("Total"), "text": item.get("taxful_total_price")},
        ]
