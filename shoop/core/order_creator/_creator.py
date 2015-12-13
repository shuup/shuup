# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal

import six
from django.utils.encoding import force_text

from shoop.core.models import Order, OrderLine, OrderLineType
from shoop.core.shortcuts import update_order_line_from_product
from shoop.core.utils.users import real_user_or_none
from shoop.front.signals import order_creator_finished
from shoop.utils.numbers import bankers_round


class OrderCreator(object):

    def __init__(self, request):
        self.request = request  # TODO: Get rid of `request`?

    def source_line_to_order_lines(self, order, source_line):
        """
        Convert a SourceLine into one or more OrderLines (yield them)
        :param order: The order
        :param source_line: The SourceLine
        """
        order_line = OrderLine(order=order)
        product = source_line.product
        quantity = Decimal(source_line.quantity)
        if product:
            order_line.product = product
            if product.sales_unit:
                quantized_quantity = bankers_round(quantity, product.sales_unit.decimals)
                if quantized_quantity != quantity:
                    raise ValueError("Sales unit decimal conversion causes precision loss!")
        else:
            order_line.product = None

        def text(value):
            return force_text(value) if value is not None else ""

        order_line.quantity = quantity
        order_line.supplier = source_line.supplier
        order_line.sku = text(source_line.sku)
        order_line.text = (text(source_line.text))[:192]
        if source_line.base_unit_price:
            order_line.base_unit_price = source_line.base_unit_price
        if source_line.discount_amount:
            order_line.discount_amount = source_line.discount_amount
        order_line.type = (source_line.type if source_line.type is not None
                           else OrderLineType.OTHER)
        order_line.accounting_identifier = text(source_line.accounting_identifier)
        order_line.require_verification = bool(source_line.require_verification)
        order_line.verified = False
        order_line.source_line = source_line
        self._check_orderability(order_line)

        yield order_line

        for child_order_line in self.create_package_children(order_line):
            yield child_order_line

    def create_package_children(self, order_line):
        order = order_line.order
        parent_product = order_line.product
        # :type parent_product: shoop.core.models.Product
        if not (parent_product and parent_product.is_package_parent()):
            return

        for child_product, child_quantity in six.iteritems(parent_product.get_package_child_to_quantity_map()):
            child_order_line = OrderLine(order=order, parent_line=order_line)
            update_order_line_from_product(
                pricing_context=self.request,
                order_line=child_order_line,
                product=child_product,
                quantity=(order_line.quantity * child_quantity),
            )
            # Package children are free
            assert child_order_line.base_unit_price.value == 0
            child_order_line.source_line = order_line.source_line
            child_order_line.supplier = order_line.supplier
            self._check_orderability(child_order_line)
            yield child_order_line

    def _check_orderability(self, order_line):
        if not order_line.product:
            return
        if not order_line.supplier:
            raise ValueError("Order line has no supplier")
        order = order_line.order
        shop_product = order_line.product.get_shop_instance(order.shop)
        shop_product.raise_if_not_orderable(
            supplier=order_line.supplier,
            quantity=order_line.quantity,
            customer=order.customer
        )

    def process_saved_order_line(self, order, order_line):
        """
        Called in sequence for all order lines to be saved into the order. These have all been saved, so they have PKs.
        :type order: Order
        :type order_line: OrderLine
        """
        pass

    def add_lines_into_order(self, order, lines):
        source_line_id_to_order_line_map = {}
        for index, order_line in enumerate(lines):
            order_line.order = order
            order_line.ordering = index
            if not order_line.require_verification:
                order_line.verified = True
            order_line.save()
            source_line = getattr(order_line, "source_line", None)
            if source_line:  # Stash which source line corresponds to which order line for the parentage pass below.
                line_id = source_line.line_id
                if line_id:
                    source_line_id_to_order_line_map[line_id] = order_line

        # One more pass to save parent relations from the source lines
        for order_line in lines:
            source_line = getattr(order_line, "source_line", None)
            if source_line:
                parent_source_line_id = source_line.parent_line_id
                parent_order_line = source_line_id_to_order_line_map.get(parent_source_line_id)
                if parent_order_line:
                    order_line.parent_line = parent_order_line
                    order_line.save()

        self.add_line_taxes(lines)

        # And one last pass to call the subclass hook.
        for order_line in lines:
            self.process_saved_order_line(order=order, order_line=order_line)

    def add_line_taxes(self, lines):
        for line in lines:
            for (index, line_tax) in enumerate(line.source_line.taxes, 1):
                line.taxes.create(
                    tax=line_tax.tax,
                    name=line_tax.tax.name,
                    amount_value=line_tax.amount.value,
                    base_amount_value=line_tax.base_amount.value,
                    ordering=index,
                )

    def get_source_order_lines(self, source, order):
        """
        :type source: shoop.core.order_creator.OrderSource
        :type order: shoop.core.models.Order
        """
        lines = []
        source.update_from_order(order)
        # Since we just updated `order_provision`, we need to uncache
        # the processed lines.
        source.uncache()
        for line in source.get_final_lines(with_taxes=True):
            lines.extend(self.source_line_to_order_lines(order, line))
        return lines

    def create_order(self, order_source):
        # order_provision.target_user = self._maybe_create_user(
        #     user=order_provision.target_user,
        #     billing_address=order_provision.billing_address,
        #     shipping_address=order_provision.shipping_address
        # )
        order = Order(
            shop=order_source.shop,
            currency=order_source.currency,
            prices_include_tax=order_source.prices_include_tax,
            shipping_method=order_source.shipping_method,
            payment_method=order_source.payment_method,
            customer_comment=order_source.customer_comment,
            marketing_permission=bool(order_source.marketing_permission),
            ip_address=(self.request.META.get("REMOTE_ADDR") if self.request else None),
            creator=real_user_or_none(order_source.creator),
            orderer=(order_source.orderer or None),
            customer=(order_source.customer or None),
            billing_address=(order_source.billing_address.to_immutable() if order_source.billing_address else None),
            shipping_address=(order_source.shipping_address.to_immutable() if order_source.shipping_address else None),
            order_date=order_source.order_date,
            status=order_source.status,
            payment_data=order_source.payment_data,
            shipping_data=order_source.shipping_data,
            extra_data=order_source.extra_data
        )
        order.save()

        self.process_order_before_lines(source=order_source, order=order)
        lines = self.get_source_order_lines(source=order_source, order=order)
        self.add_lines_into_order(order, lines)

        if any(line.require_verification for line in order.lines.all()):
            order.require_verification = True
            order.all_verified = False
        else:
            order.all_verified = True

        order.cache_prices()
        order.save()

        order_creator_finished.send(OrderCreator, order=order, source=order_source, request=self.request)

        order.save()
        self.process_order_after_lines(source=order_source, order=order)

        # Then do all the caching one more time!
        order.cache_prices()
        order.save()
        return order
    #
    # def assign_campaign_usages(self, order, campaign_to_code):
    #     from shoop.shop.models.campaigns import OrderCampaignUsage
    #
    #     for campaign, campaign_code in campaign_to_code.iteritems():
    #         OrderCampaignUsage.objects.create(
    #             order=order,
    #             campaign=campaign,
    #             code=campaign_code
    #         )

    def process_order_before_lines(self, source, order):
        # Subclass hook
        pass

    def process_order_after_lines(self, source, order):
        # Subclass hook
        pass
