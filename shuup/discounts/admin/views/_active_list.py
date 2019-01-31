# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.picotable import Column, DateRangeFilter, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.discounts.models import Discount
from shuup.utils.i18n import (
    format_money, format_number, format_percent,
    get_locally_formatted_datetime
)


class DiscountListView(PicotableListView):
    model = Discount
    url_identifier = "discounts"

    default_columns = [
        Column(
            "name", _("Discount Name"), sort_field="name", display="name",
            filter_config=TextFilter(filter_field="name", placeholder=_("Filter by name..."))
        ),
        Column(
            "product__translations__name", _("Product"), display="product",
            filter_config=TextFilter(filter_field="product__translations__name", placeholder=_("Filter by product..."))
        ),
        Column(
            "category", _("Category"), display="category",
            filter_config=TextFilter(
                filter_field="category__translations__name", placeholder=_("Filter by category..."))
        ),
        Column(
            "contact_group", _("Contact Group"), display="contact_group",
            filter_config=TextFilter(
                filter_field="contact_group__translations__name", placeholder=_("Filter by contact group..."))
        ),
        Column(
            "contact", _("Contact"), display="contact",
            filter_config=TextFilter(filter_field="contact__translations__name", placeholder=_("Filter by contact..."))
        ),
        Column(
            "coupon_code", _("Coupon code"), display="coupon_code",
            filter_config=TextFilter(filter_field="coupon_code__code", placeholder=_("Filter by coupon code..."))
        ),
        Column("discount_effect", _("Effect"), display="get_discount_effect"),
        Column(
            "end_datetime", _("End Date and Time"), display="format_end_datetime", filter_config=DateRangeFilter()
        )
    ]

    mass_actions = [
        "shuup.discounts.admin.mass_actions:ArchiveMassAction"
    ]

    toolbar_buttons_provider_key = "discount_list_toolbar_provider"
    mass_actions_provider_key = "discount_list_actions_provider"

    def get_discount_effect(self, instance):
        if not (instance.discount_amount_value or instance.discounted_price_value or instance.discount_percentage):
            return "-"

        effects = []
        shop = get_shop(self.request)
        if instance.discount_amount_value:
            effects.append(
                "- %s" % format_money(shop.create_price(instance.discount_amount_value))
                if shop else format_number(instance.discount_amount_value))

        if instance.discounted_price_value:
            effects.append(
                format_money(shop.create_price(instance.discounted_price_value))
                if shop else format_number(instance.discounted_price_value))

        if instance.discount_percentage:
            effects.append(format_percent(instance.discount_percentage))

        return ','.join(effects)

    def format_end_datetime(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.end_datetime) if instance.end_datetime else ""

    def get_queryset(self):
        return Discount.objects.active(get_shop(self.request))
