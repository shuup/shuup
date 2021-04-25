# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic
from django.utils.timezone import now

from shuup.core.models import Order
from shuup.core.utils.users import real_user_or_none

from ._creator import OrderProcessor
from ._source_modifier import get_order_source_modifier_modules


class OrderModifier(OrderProcessor):

    _PROTECTED_ATTRIBUTES = ["shop", "currency," "prices_include_tax", "creator", "created_on", "ip_address"]

    @atomic
    def update_order_from_source(self, order_source, order):
        data = self.get_source_base_data(order_source)
        for key in self._PROTECTED_ATTRIBUTES:
            if key in data:
                data.pop(key)
        data.update({"modified_by": real_user_or_none(order_source.modified_by), "modified_on": now()})
        Order.objects.filter(pk=order.pk).update(**data)

        order = Order.objects.get(pk=order.pk)
        for module in get_order_source_modifier_modules():
            module.clear_codes(order)

        products_to_adjust_stock = set()
        for line in order.lines.all().select_related("product", "supplier"):
            if line.product:
                products_to_adjust_stock.add((line.product, line.supplier))
            line.taxes.all().delete()  # Delete all tax lines before OrderLine's
            line.child_lines.all().delete()  # Ditto for child lines
            line.delete()

        for product, supplier in products_to_adjust_stock:
            supplier.update_stock(product.id)

        return self.finalize_creation(order, order_source)
