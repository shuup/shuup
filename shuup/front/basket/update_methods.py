# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.contrib import messages

from shuup.core.models import Product, Supplier
from shuup.utils.numbers import parse_decimal_string


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
        if line:
            return self.basket.delete_line(line["line_id"])

    def _get_orderability_errors(self, product, supplier, delta):
        basket_quantities = self.basket.get_product_ids_and_quantities()
        product_basket_quantity = basket_quantities.get(product.id, 0)
        total_product_quantity = delta + product_basket_quantity
        shop_product = product.get_shop_instance(shop=self.request.shop)
        errors = list(shop_product.get_orderability_errors(
            supplier=supplier,
            customer=self.basket.customer,
            quantity=total_product_quantity
        ))
        if product.is_package_parent():
            for child_product, child_quantity in six.iteritems(product.get_package_child_to_quantity_map()):
                child_basket_quantity = basket_quantities.get(child_product.id, 0)
                total_child_quantity = (delta * child_quantity) + child_basket_quantity
                shop_product = child_product.get_shop_instance(shop=self.request.shop)
                child_errors = list(shop_product.get_orderability_errors(
                    supplier=supplier,
                    customer=self.basket.customer,
                    quantity=total_child_quantity
                ))
                errors.extend(child_errors)
        return errors

    def update_quantity(self, line, value, **kwargs):
        new_quantity = int(parse_decimal_string(value))  # TODO: The quantity could be a non-integral value
        if new_quantity is None:
            return False

        if not (line and line["quantity"] != new_quantity):
            return False

        changed = False

        # Ensure sub-lines also get changed accordingly
        linked_lines = [line] + list(self.basket.find_lines_by_parent_line_id(line["line_id"]))
        orderable_line_ids = [basket_line.line_id for basket_line in self.basket.get_lines()]

        for linked_line in linked_lines:
            if linked_line["line_id"] not in orderable_line_ids:
                # Customer can change quantity in non-orderable lines regardless
                linked_line["quantity"] = new_quantity
                changed = True
            else:
                product = Product.objects.get(pk=linked_line["product_id"])
                supplier = Supplier.objects.filter(pk=linked_line.get("supplier_id", 0)).first()

                # Basket quantities already contain current quantities for orderable lines
                quantity_delta = new_quantity - line["quantity"]
                errors = self._get_orderability_errors(product, supplier, quantity_delta)
                if errors:
                    for error in errors:
                        error_texts = ", ".join(six.text_type(sub_error) for sub_error in error)
                        message = u"%s: %s" % (linked_line.get("text") or linked_line.get("name"), error_texts)
                        messages.warning(self.request, message)
                    continue
                self.basket.update_line(linked_line, quantity=new_quantity)
                linked_line["quantity"] = new_quantity
                changed = True

        return changed
