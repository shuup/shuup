# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.contexts import PriceTaxContext
from shoop.core.models import OrderLineType


def update_order_line_from_product(request, order_line, product, quantity=1, supplier=None):
    """
    This is a convenience method for simple applications.
    """

    if order_line.pk:  # pragma: no cover
        raise Exception("set_from_product may not be used on saved lines")

    if not product:  # pragma: no cover
        raise Exception("set_from_product may not be used without product")

    # TODO: (TAX) Taxes in update_order_line_from_product
    context = PriceTaxContext.from_request(request)
    price = product.get_price(context, quantity=quantity)
    order_line.supplier = supplier
    order_line.type = OrderLineType.PRODUCT
    order_line.product = product
    order_line.quantity = quantity
    order_line.sku = product.sku
    order_line.name = product.safe_translation_getter("name") or product.sku
    order_line.accounting_identifier = product.accounting_identifier
    order_line.require_verification = bool(getattr(product, "require_verification", False))
    order_line.verified = False
    order_line.unit_price = price
