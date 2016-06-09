# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.campaigns.models.contact_group_sales_ranges import \
    ContactGroupSalesRange

from .utils import assign_to_group_based_on_sales


def update_customers_groups(sender, instance, **kwargs):
    if not instance.order.customer:
        return
    assign_to_group_based_on_sales(ContactGroupSalesRange, instance.order.shop, instance.order.customer)
