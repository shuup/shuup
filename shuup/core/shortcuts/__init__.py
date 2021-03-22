# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import OrderLineType


def update_order_line_from_product(pricing_context, order_line, product, quantity=1, supplier=None):
    """
    Update OrderLine data from a product.

    This is a convenience method for simple applications.

    :type pricing_context: shuup.core.pricing.PricingContextable|None
    :param pricing_context:
      Pricing context to use for pricing the line.  If None is given,
      the line will get zero price and zero discount amount.
    :type order_line: shuup.core.models.OrderLine
    :type product: shuup.core.models.Product
    :type quantity: int|decimal.Decimal
    :type supplier: shuup.core.models.Supplier|None
    """

    if order_line.pk:  # pragma: no cover
        raise Exception("Error! `set_from_product` may not be used on saved lines.")

    if not product:  # pragma: no cover
        raise Exception("Error! `set_from_product` may not be used without product.")

    order_line.supplier = supplier
    order_line.type = OrderLineType.PRODUCT
    order_line.product = product
    order_line.quantity = quantity
    order_line.sku = product.sku
    order_line.text = product.safe_translation_getter("name") or product.sku
    order_line.accounting_identifier = product.accounting_identifier
    order_line.require_verification = bool(getattr(product, "require_verification", False))
    order_line.verified = False
    if pricing_context:
        price_info = product.get_price_info(pricing_context, quantity=quantity)
        order_line.base_unit_price = price_info.base_unit_price
        order_line.discount_amount = price_info.discount_amount
        assert order_line.price == price_info.price
    else:
        order_line.base_unit_price_value = 0
        order_line.discount_amount_value = 0
