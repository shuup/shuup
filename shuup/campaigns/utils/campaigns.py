# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import Counter


def get_lines_suppliers(basket):
    """
    Returns a list of all suppliers from the basket
    """
    suppliers = set()
    for line in basket.get_lines():
        if line.supplier:
            suppliers.add(line.supplier)
    return suppliers


def get_product_ids_and_quantities(basket, supplier=None):
    q_counter = Counter()
    for line in basket.get_lines():
        if not line.product:
            continue
        if supplier and line.supplier != supplier:
            continue
        q_counter[line.product.id] += line.quantity
        if line.product.variation_parent_id:
            q_counter[line.product.variation_parent_id] += line.quantity
    return dict(q_counter.most_common())


def get_total_price_of_products(basket, campaign):
    total_of_products = basket.shop.create_price(0)
    product_lines = basket.get_product_lines()
    if hasattr(campaign, "supplier") and campaign.supplier:
        product_lines = [line for line in product_lines if line.supplier == campaign.supplier]

    for product_line in product_lines:
        total_of_products += product_line.price
    return total_of_products
