# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Case, When


def order_query_by_values(initial_q, values):
    order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(values)])
    return initial_q.order_by(order)
