# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from shuup.admin.base import Section
from shuup.core.models import Order


class ProductOrdersSection(Section):
    identifier = "product_orders"
    name = _("Orders")
    icon = "fa-inbox"
    template = "shuup/admin/products/_product_orders.jinja"
    order = 1

    @staticmethod
    def visible_for_object(product):
        return bool(product.pk)

    @staticmethod
    def get_context_data(product):
        # TODO: restrict to first 100 orders - do pagination later
        return Order.objects.valid().filter(lines__product_id=product.id).distinct()[:100]
