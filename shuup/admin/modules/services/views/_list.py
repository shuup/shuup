# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    Column, TextFilter, true_or_false_filter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import PaymentMethod, ShippingMethod
from shuup.utils.django_compat import force_text


class ServiceListView(PicotableListView):
    model = None  # Override in subclass
    columns = []
    base_columns = [
        Column(
            "name", _("Name"), sort_field="translations__name",
            filter_config=TextFilter(filter_field="translations__name", placeholder=_("Filter by name..."))
        ),
        Column(
            "choice_identifier", _(u"Service choice"), display="format_service_choice",
            sortable=False,
        ),
        Column("enabled", _(u"Enabled"), filter_config=true_or_false_filter),
        Column("shop", _(u"Shop"))
    ]
    toolbar_buttons_provider_key = "service_list_toolbar_provider"
    mass_actions_provider_key = "service_list_mass_actions_provider"

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
        ]

    def format_service_choice(self, instance, *args, **kwargs):
        if instance.provider:
            for choice in instance.provider.get_service_choices():
                if choice.identifier == instance.choice_identifier:
                    return force_text(choice.name)

    def get_queryset(self):
        return super(ServiceListView, self).get_queryset().filter(shop=self.request.shop)


class ShippingMethodListView(ServiceListView):
    model = ShippingMethod

    def __init__(self, **kwargs):
        self.default_columns = self.base_columns + [Column("carrier", _("Carrier"))]
        super(ShippingMethodListView, self).__init__(**kwargs)


class PaymentMethodListView(ServiceListView):
    model = PaymentMethod

    def __init__(self, **kwargs):
        self.default_columns = self.base_columns + [Column("payment_processor", _("Payment Processor"))]
        super(PaymentMethodListView, self).__init__(**kwargs)
