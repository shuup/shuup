# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.core.exceptions import ValidationError

from shuup.core.models import ShopProduct
from shuup.core.order_creator import OrderLineBehavior
from shuup.utils.numbers import parse_decimal_string


class BasketUpdateMethods(object):
    def __init__(self, request, basket):
        """
        Initialize.

        :type request: django.http.HttpRequest
        :type basket: shuup.front.basket.objects.BaseBasket
        """
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
            'dq_': self.update_display_quantity,
            'delete_': self.delete_line,
        }

    def delete_line(self, line, **kwargs):
        if line:
            return self.basket.delete_line(line["line_id"])

    def _get_orderability_errors(self, product, supplier, delta):
        basket_quantities = self.basket.get_product_ids_and_quantities()
        product_basket_quantity = basket_quantities.get(product.id, 0)
        total_product_quantity = delta + product_basket_quantity
        try:
            shop_product = product.get_shop_instance(shop=self.request.shop)
        except ShopProduct.DoesNotExist:
            return [
                ValidationError("Error! %s is not available in %s." % (product, self.request.shop),
                                code="product_not_available_in_shop")
            ]

        errors = list(shop_product.get_orderability_errors(
            supplier=supplier,
            customer=self.basket.customer,
            quantity=total_product_quantity
        ))
        if product.is_package_parent():
            for child_product, child_quantity in six.iteritems(product.get_package_child_to_quantity_map()):
                child_basket_quantity = basket_quantities.get(child_product.id, 0)
                total_child_quantity = (delta * child_quantity) + child_basket_quantity
                try:
                    shop_product = child_product.get_shop_instance(shop=self.request.shop)
                except ShopProduct.DoesNotExist:
                    child_errors = [
                        ValidationError(
                            "Error! %s is not available in %s." % (child_product, self.request.shop),
                            code="product_not_available_in_shop"
                        )
                    ]
                else:
                    child_errors = list(shop_product.get_orderability_errors(
                        supplier=supplier,
                        customer=self.basket.customer,
                        quantity=total_child_quantity
                    ))
                errors.extend(child_errors)
        return errors

    def update_display_quantity(self, line, value, **kwargs):
        if not line:
            return False
        new_display_quantity = parse_decimal_string(value)
        if new_display_quantity is None:
            return False
        basket_line = self.basket.get_basket_line(line['line_id'])
        if basket_line and basket_line.product:
            unit = basket_line.shop_product.unit
            new_quantity = unit.from_display(new_display_quantity)
        else:
            new_quantity = new_display_quantity
        return self._update_quantity(line, new_quantity)

    def update_quantity(self, line, value, **kwargs):
        new_quantity = parse_decimal_string(value)
        if new_quantity is None:
            return False
        return self._update_quantity(line, new_quantity)

    def _handle_orderability_error(self, line, error):
        raise error

    def _update_quantity(self, line, new_quantity):
        if not (line and line["quantity"] != new_quantity):
            return False

        changed = False

        # Ensure sub-lines also get changed accordingly
        linked_lines = [line] + list(self.basket.find_lines_by_parent_line_id(line["line_id"]))
        orderable_lines = {
            basket_line.line_id: basket_line
            for basket_line in self.basket.get_lines()
        }

        for linked_line in linked_lines:
            orderable_line = orderable_lines.get(linked_line["line_id"])

            # Use default OrderLineBehaviour
            line_behavior = linked_line.get("on_parent_change_behavior", OrderLineBehavior.INHERIT)

            if not orderable_line:
                # Customer can change quantity in non-orderable lines regardless
                linked_line["quantity"] = new_quantity
                changed = True
            elif line_behavior == OrderLineBehavior.DELETE:
                linked_line["quantity"] = 0
                changed = True
            elif line_behavior == OrderLineBehavior.SKIP:
                continue

            # then line_behavior == OrderLineBehavior.INHERIT
            else:
                product = orderable_line.product
                supplier = orderable_line.supplier

                # Basket quantities already contain current quantities for orderable lines
                quantity_delta = new_quantity - line["quantity"]

                # check orderability errors if the line contains a product
                if product:
                    errors = self._get_orderability_errors(product, supplier, quantity_delta)
                    if errors:
                        for error in errors:
                            self._handle_orderability_error(line, error)
                        continue

                self.basket.update_line(linked_line, quantity=new_quantity)
                linked_line["quantity"] = new_quantity
                changed = True

        return changed
