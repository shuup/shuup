# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.models import OrderLineType


def update_order_line_from_product(
        pricing_context, order_line, product, quantity=1, supplier=None):
    """
    Update OrderLine data from a product.

    This is a convenience method for simple applications.

    :type pricing_context: shoop.core.pricing.PricingContextable
    :type order_line: shoop.core.models.OrderLine
    :type product: shoop.core.models.Product
    :type quantity: int|decimal.Decimal
    :type supplier: shoop.core.models.Supplier|None
    """

    if order_line.pk:  # pragma: no cover
        raise Exception("set_from_product may not be used on saved lines")

    if not product:  # pragma: no cover
        raise Exception("set_from_product may not be used without product")

    price_info = product.get_price_info(pricing_context, quantity=quantity)
    order_line.supplier = supplier
    order_line.type = OrderLineType.PRODUCT
    order_line.product = product
    order_line.quantity = quantity
    order_line.sku = product.sku
    order_line.name = product.safe_translation_getter("name") or product.sku
    order_line.accounting_identifier = product.accounting_identifier
    order_line.require_verification = bool(getattr(product, "require_verification", False))
    order_line.verified = False
    order_line.base_unit_price = price_info.base_unit_price
    order_line.discount_amount = price_info.discount_amount
    assert order_line.price == price_info.price
