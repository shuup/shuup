# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.modules.sales_dashboard.dashboard import \
    OrderValueChartDashboardBlock
from shuup.testing.factories import (
    create_random_order, create_random_person, get_default_product
)


@pytest.mark.django_db
def test_order_chart_works():
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    chart = OrderValueChartDashboardBlock("test", order.currency).get_chart()
    assert len(chart.series[0]) > 0
