# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import warnings
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text

from shuup.core.models import Order, OrderLine, OrderLineType, ShopProduct
from shuup.core.order_creator.signals import (
    order_creator_finished, post_order_line_save
)
from shuup.core.shortcuts import update_order_line_from_product
from shuup.core.utils import context_cache
from shuup.core.utils.users import real_user_or_none
from shuup.utils.deprecation import RemovedFromShuupWarning
from shuup.utils.numbers import bankers_round

from ._source_modifier import get_order_source_modifier_modules


class OrderProcessor(object):

    def source_line_to_order_lines(self, order, source_line):
        """
        Convert a source line into one or more order lines.

        Normally each source line will yield just one order line, but package
        products will yield lines for both the parent and its children products.

        :type order: shuup.core.models.Order
        :param order: The order.
        :type source_line: shuup.core.order_creator.SourceLine
        :param source_line: The SourceLine.
        :rtype: Iterable[OrderLine]
        """
        order_line = OrderLine(order=order)
        product = source_line.product
        quantity = Decimal(source_line.quantity)
        if product:
            order_line.product = product
            if product.sales_unit:
                quantized_quantity = bankers_round(quantity, product.sales_unit.decimals)
                if quantized_quantity != quantity:
                    raise ValueError("Error! Sales unit decimal conversion causes precision loss.")
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
        order_line.verified = (not order_line.require_verification)
        order_line.source_line = source_line
        order_line.parent_source_line = source_line.parent_line
        extra_data = source_line.data.get("extra", {}) if hasattr(source_line, "data") else {}
        extra_data.update({"source_line_id": source_line.line_id})

        order_line.extra_data = extra_data
        self._check_orderability(order_line)

        yield order_line

        for child_order_line in self.create_package_children(order_line):
            yield child_order_line

    def create_package_children(self, order_line):
        order = order_line.order
        parent_product = order_line.product
        # :type parent_product: shuup.core.models.Product
        if not (parent_product and parent_product.is_package_parent()):
            return

        child_to_quantity = parent_product.get_package_child_to_quantity_map()
        for (child_product, child_quantity) in child_to_quantity.items():
            child_order_line = OrderLine(order=order, parent_line=order_line)
            update_order_line_from_product(
                pricing_context=None,  # Will use zero price
                order_line=child_order_line,
                product=child_product,
                quantity=(order_line.quantity * child_quantity),
            )
            # Package children are free
            assert child_order_line.base_unit_price.value == 0
            child_order_line.source_line = None
            child_order_line.parent_source_line = order_line.source_line
            child_order_line.supplier = order_line.supplier
            self._check_orderability(child_order_line)
            yield child_order_line

    def _check_orderability(self, order_line):
        if not order_line.product:
            return
        if not order_line.supplier:
            raise ValueError("Error! Order line has no supplier.")
        order = order_line.order
        try:
            shop_product = order_line.product.get_shop_instance(order.shop)
        except ShopProduct.DoesNotExist:
            raise ValidationError(
                "Error! %s is not available in %s." % (order_line.product, order.shop),
                code="invalid_shop"
            )

        shop_product.raise_if_not_orderable(
            supplier=order_line.supplier,
            quantity=order_line.quantity,
            customer=order.customer
        )

    def process_saved_order_line(self, order, order_line):
        """
        Called in sequence for all order lines to be saved into the order.
        These have all been saved, so they have PKs.

        :type order: Order
        :type order_line: OrderLine
        """
        pass

    def add_lines_into_order(self, order, lines):
        # Map source lines to order lines for parentage linking
        order_line_by_source = {
            id(order_line.source_line): order_line
            for order_line in lines
        }

        # Set line ordering, parentage and save the lines
        for index, order_line in enumerate(lines):
            order_line.order = order
            order_line.ordering = index

            parent_src_line = order_line.parent_source_line
            if parent_src_line:
                parent_order_line = order_line_by_source[id(parent_src_line)]
                assert parent_order_line.pk, "Parent line should be saved"
                order_line.parent_line = parent_order_line

            order_line.save()

        self.add_line_taxes(lines)

        # And one last pass to call the subclass hook.
        for order_line in lines:
            self.process_saved_order_line(order=order, order_line=order_line)
            post_order_line_save.send(sender=type(self), order=order, order_line=order_line)

    def add_line_taxes(self, lines):
        for line in lines:
            if not line.source_line:
                continue  # Cannot have taxes, since not in source
            for (index, line_tax) in enumerate(line.source_line.taxes, 1):
                line.taxes.create(
                    tax=line_tax.tax,
                    name=line_tax.name,
                    amount_value=line_tax.amount.value,
                    base_amount_value=line_tax.base_amount.value,
                    ordering=index,
                )

    def get_source_order_lines(self, source, order):
        """
        :type source: shuup.core.order_creator.OrderSource
        :type order: shuup.core.models.Order
        :rtype: list[OrderLine]
        """
        lines = []
        source.update_from_order(order)
        # Since we just updated `order_provision`, we need to uncache
        # the processed lines.
        source.uncache()
        for line in source.get_final_lines(with_taxes=True):
            lines.extend(self.source_line_to_order_lines(order, line))
        return lines

    def get_source_base_data(self, order_source):
        """
        :type order_source: shuup.core.order_creator.OrderSource
        """
        return dict(
            shop=order_source.shop,
            currency=order_source.currency,
            prices_include_tax=order_source.prices_include_tax,
            shipping_address=(order_source.shipping_address.to_immutable() if order_source.shipping_address else None),
            billing_address=(order_source.billing_address.to_immutable() if order_source.billing_address else None),
            customer=(order_source.customer or None),
            orderer=(order_source.orderer or None),
            creator=real_user_or_none(order_source.creator),
            shipping_method=order_source.shipping_method,
            payment_method=order_source.payment_method,
            customer_comment=(order_source.customer_comment if order_source.customer_comment else ""),
            marketing_permission=bool(order_source.marketing_permission),
            language=order_source.language,
            ip_address=order_source.ip_address,
            order_date=order_source.order_date,
            status=order_source.status,
            payment_data=order_source.payment_data,
            shipping_data=order_source.shipping_data,
            extra_data=order_source.extra_data
        )

    def finalize_creation(self, order, order_source):
        order_source.verify_orderability()
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

        self._update_customer_info_if_needed(order)
        self._assign_code_usages(order_source, order)

        order.save()
        self.process_order_after_lines(source=order_source, order=order)

        # Then do all the caching one more time!
        order.cache_prices()
        order.save()
        return order

    def _update_customer_info_if_needed(self, order):
        if not order.customer:
            return

        changed_fields = []
        if not order.customer.name and order.billing_address:
            order.customer.name = order.billing_address.name
            changed_fields.append("name")

        for address_kind in ["billing_address", "shipping_address"]:
            order_addr = getattr(order, address_kind, None)
            if not order_addr:
                continue
            customer_address_field = "default_%s" % address_kind
            if not getattr(order.customer, customer_address_field, None):
                new_customer_address = order_addr.to_mutable()
                new_customer_address.save()
                setattr(order.customer, customer_address_field, new_customer_address)
                changed_fields.append(customer_address_field)

        if order.customer.marketing_permission != order.marketing_permission:
            order.customer.marketing_permission = order.marketing_permission
            changed_fields.append("marketing_permission")

        if changed_fields:
            order.customer.save()

        # add shop to the customer shop list if needed
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS and settings.SHUUP_MANAGE_CONTACTS_PER_SHOP:
            order.customer.add_to_shop(order.shop)

    def _assign_code_usages(self, order_source, order):
        order.codes = order_source.codes
        for code in order_source.codes:
            self._assign_code_usage(order_source, order, code)

    def _assign_code_usage(self, order_source, order, code):
        for module in get_order_source_modifier_modules():
            if module.can_use_code(order_source, code):
                module.use_code(order, code)
                break

    def process_order_before_lines(self, source, order):
        # Subclass hook
        pass

    def process_order_after_lines(self, source, order):
        # Subclass hook
        pass


class OrderCreator(OrderProcessor):

    def __init__(self, request=None):
        """
        Initialize order creator.

        :type request: django.http.HttpRequest|None
        :param request:
          Optional request object for backward compatibility. Passing
          non-None value is DEPRECATED.
        """
        if request is not None:
            warnings.warn(
                "Warning! Initializing `OrderCreator` with a `request` is deprecated.",
                RemovedFromShuupWarning, stacklevel=2)

    def create_order(self, order_source):
        data = self.get_source_base_data(order_source)
        order = Order(**data)
        order.save()
        order = self.finalize_creation(order, order_source)
        order_creator_finished.send(sender=type(self), order=order, source=order_source)
        # reset product prices
        for line in order.lines.exclude(product_id=None):
            context_cache.bump_cache_for_product(line.product, shop=order.shop)
        return order
