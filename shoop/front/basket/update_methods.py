# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.contrib import messages

from shoop.core.models import Product, Supplier
from shoop.utils.numbers import parse_decimal_string


class BasketUpdateMethods(object):
    def __init__(self, request, basket):
        self.request = request
        self.basket = basket

    def get_prefix_to_method_map(self):
        """Override this method to link prefixes with their associated methods to call.

        Format of the dictionary is: { FIELD_NAME_PREFIX: METHOD }.

        METHOD is a function which accepts the keyword arguments given in `update_basket_contents`. It should perform
        the necessary changes to the basket_line and then return whether the value had changed or not.
        (See `update_quantity` or `delete_line` for examples.)
        """

        return {
            'q_': self.update_quantity,
            'delete_': self.delete_line,
        }

    def delete_line(self, line, **kwargs):
        return self.basket.delete_line(line["line_id"])

    def _get_orderability_errors(self, basket_line, new_quantity):
        product = Product.objects.get(pk=basket_line["product_id"])
        shop_product = product.get_shop_instance(shop=self.request.shop)
        supplier = Supplier.objects.filter(pk=basket_line.get("supplier_id", 0)).first()
        return shop_product.get_orderability_errors(
            supplier=supplier,
            customer=self.basket.customer,
            quantity=new_quantity
        )

    def update_quantity(self, line, value, **kwargs):
        new_quantity = int(parse_decimal_string(value))  # TODO: The quantity could be a non-integral value
        if new_quantity is None:
            return False

        if not (line and line["quantity"] != new_quantity):
            return False

        changed = False

        # Ensure sub-lines also get changed accordingly
        linked_lines = [line] + list(self.basket.find_lines_by_parent_line_id(line["line_id"]))
        for linked_line in linked_lines:
            errors = list(self._get_orderability_errors(linked_line, new_quantity))
            if errors:
                error_texts = ", ".join(six.text_type(error) for error in errors)
                message = u"%s: %s" % (linked_line.get("text") or linked_line.get("name"), error_texts)
                messages.warning(self.request, message)
                continue
            self.basket.update_line(linked_line, quantity=new_quantity)
            linked_line["quantity"] = new_quantity
            changed = True

        return changed
