# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import Counter


def get_product_ids_and_quantities(basket):
    q_counter = Counter()
    for line in basket.get_lines():
        if not line.product:
            continue
        q_counter[line.product.id] += line.quantity
        if line.product.variation_parent_id:
            q_counter[line.product.variation_parent_id] += line.quantity
    return dict(q_counter.most_common())
