# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import (
    Column, TextFilter, true_or_false_filter
)
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import PaymentMethod, ShippingMethod


class ServiceListView(PicotableListView):
    model = None  # Override in subclass
    columns = [
        Column(
            "name", _("Name"), sort_field="translations__name",
            filter_config=TextFilter(filter_field="name", placeholder=_("Filter by name..."))
        ),
        Column("enabled", _(u"Enabled"), filter_config=true_or_false_filter),
        Column("shop", _(u"Shop"))
    ]

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
        ]


class ShippingMethodListView(ServiceListView):
    model = ShippingMethod

    def __init__(self, **kwargs):
        self.columns += [Column("carrier", _("Carrier"))]
        super(ShippingMethodListView, self).__init__(**kwargs)


class PaymentMethodListView(ServiceListView):
    model = PaymentMethod

    def __init__(self, **kwargs):
        self.columns += [Column("payment_processor", _("Payment Processor"))]
        super(PaymentMethodListView, self).__init__(**kwargs)
