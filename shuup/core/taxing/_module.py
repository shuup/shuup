# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import abc
import six
from collections import defaultdict
from django.conf import settings
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from itertools import chain
from typing import TYPE_CHECKING, Union

from shuup.apps.provides import load_module
from shuup.core.excs import (
    InvalidRefundAmountException,
    RefundArbitraryRefundsNotAllowedException,
    RefundExceedsAmountException,
    RefundExceedsQuantityException,
)
from shuup.core.pricing import TaxfulPrice
from shuup.utils.money import Money

from ._context import TaxingContext
from .utils import get_tax_class_proportions

if TYPE_CHECKING:
    from shuup.core.models import Order
    from shuup.core.order_creator import OrderSource


def get_tax_module():
    """
    Get the TaxModule specified in settings.

    :rtype: shuup.core.taxing.TaxModule
    """
    return load_module("SHUUP_TAX_MODULE", "tax_module")()


def should_calculate_taxes_automatically():
    """
    If ``settings.SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE``
    is False taxes shouldn't be calculated automatically otherwise
    use current tax module value ``TaxModule.calculating_is_cheap``
    to determine whether taxes should be calculated automatically.

    :rtype: bool
    """
    if not settings.SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE:
        return False
    return get_tax_module().calculating_is_cheap


class TaxModule(six.with_metaclass(abc.ABCMeta)):
    """
    Module for calculating taxes.
    """

    identifier = None
    name = None

    calculating_is_cheap = True
    taxing_context_class = TaxingContext

    def get_context_from_request(self, request):
        customer = getattr(request, "customer", None)
        return self.get_context_from_data(customer=customer)

    def get_context_from_data(self, **context_data):
        customer = context_data.get("customer")
        customer_tax_group = context_data.get("customer_tax_group") or (customer.tax_group if customer else None)
        customer_tax_number = context_data.get("customer_tax_number") or getattr(customer, "tax_number", None)
        location = (
            context_data.get("location")
            or context_data.get("shipping_address")
            or (customer.default_shipping_address if customer else None)
            or context_data.get("billing_address")
            or (customer.default_billing_address if customer else None)
        )
        return self.taxing_context_class(
            customer_tax_group=customer_tax_group,
            customer_tax_number=customer_tax_number,
            location=location,
        )

    def get_context_from_order_source(self, source: "Union[OrderSource, Order]"):
        from shuup.core.models import Order
        from shuup.core.order_creator import OrderSource

        if isinstance(source, OrderSource):
            if source.has_shippable_lines():
                location = source.shipping_address
            else:
                location = source.billing_address

        elif isinstance(source, Order):
            from shuup.core.models import ShippingMode

            # if there is some line that is shippable, use the shipping address
            if source.lines.products().filter(product__shipping_mode=ShippingMode.SHIPPED).exists():
                location = source.shipping_address
            else:
                location = source.billing_address

        return self.get_context_from_data(customer=source.customer, location=location)

    def add_taxes(self, source, lines):
        """
        Add taxes to given OrderSource lines.

        Given lines are modified in-place, also new lines may be added
        (with ``lines.extend`` for example).  If there is any existing
        taxes for the `lines`, they are simply replaced.

        :type source: shuup.core.order_creator.OrderSource
        :param source: OrderSource of the lines
        :type lines: list[shuup.core.order_creator.SourceLine]
        :param lines: List of lines to add taxes for
        """
        context = self.get_context_from_order_source(source)
        lines_without_tax_class = []
        taxed_lines = []
        for (idx, line) in enumerate(lines):
            # this line doesn't belong to this source, ignore it
            if line.source != source:
                continue

            if line.tax_class is None:
                lines_without_tax_class.append(line)
            else:
                line.taxes = self._get_line_taxes(context, line)
                taxed_lines.append(line)

        if lines_without_tax_class:
            tax_class_proportions = get_tax_class_proportions(taxed_lines)
            self._add_proportional_taxes(context, tax_class_proportions, lines_without_tax_class)

    def _add_proportional_taxes(self, context, tax_class_proportions, lines):
        if not tax_class_proportions:
            return

        for line in lines:
            price = line.price
            line.taxes = list(
                chain.from_iterable(
                    self.get_taxed_price(context, price * factor, tax_class).taxes
                    for (tax_class, factor) in tax_class_proportions
                )
            )

    def _get_line_taxes(self, context, line):
        """
        Get taxes for given source line of an order source.

        :type context: TaxingContext
        :type line: shuup.core.order_creator.SourceLine
        :rtype: Iterable[LineTax]
        """
        taxed_price = self.get_taxed_price_for(context, line, line.price)
        return taxed_price.taxes

    def get_taxed_price_for(self, context, item, price):
        """
        Get TaxedPrice for taxable item.

        Taxable items could be products (`~shuup.core.models.Product`),
        services (`~shuup.core.models.Service`), or lines
        (`~shuup.core.order_creator.SourceLine`).

        :param context: Taxing context to calculate in
        :type context: TaxingContext
        :param item: Item to get taxes for
        :type item: shuup.core.taxing.TaxableItem
        :param price: Price (taxful or taxless) to calculate taxes for
        :type price: shuup.core.pricing.Price

        :rtype: shuup.core.taxing.TaxedPrice
        """
        return self.get_taxed_price(context, price, item.tax_class)

    @abc.abstractmethod
    def get_taxed_price(self, context, price, tax_class):
        """
        Get TaxedPrice for price and tax class.

        :param context: Taxing context to calculate in
        :type context: TaxingContext
        :param price: Price (taxful or taxless) to calculate taxes for
        :type price: shuup.core.pricing.Price
        :param tax_class: Tax class of the item to get taxes for
        :type tax_class: shuup.core.models.TaxClass

        :rtype: shuup.core.taxing.TaxedPrice
        """
        pass

    def _get_tax_class_proportions(self, order):
        product_lines = order.lines.products()

        zero = Money(0, order.currency)

        total_by_tax_class = defaultdict(lambda: zero)
        total = zero

        for line in product_lines:
            total_by_tax_class[line.product.tax_class] += line.price
            total += line.price

        if not total:
            # Can't calculate proportions, if total is zero
            return []

        return [(tax_class, tax_class_total / total) for (tax_class, tax_class_total) in total_by_tax_class.items()]

    def _refund_amount(self, context, order, index, text, amount, tax_proportions, supplier=None):
        taxes = list(
            chain.from_iterable(
                self.get_taxed_price(context, TaxfulPrice(amount * factor), tax_class).taxes
                for (tax_class, factor) in tax_proportions
            )
        )

        base_amount = amount
        if not order.prices_include_tax:
            base_amount /= 1 + sum([tax.tax.rate for tax in taxes])

        from shuup.core.models import OrderLine, OrderLineType

        refund_line = OrderLine.objects.create(
            text=text,
            order=order,
            type=OrderLineType.REFUND,
            ordering=index,
            base_unit_price_value=-base_amount,
            quantity=1,
            supplier=supplier,
        )
        for line_tax in taxes:
            refund_line.taxes.create(
                tax=line_tax.tax,
                name=_("Refund for %s" % line_tax.name),
                amount_value=-line_tax.amount,
                base_amount_value=-line_tax.base_amount,
                ordering=1,
            )
        return refund_line

    @transaction.atomic  # noqa (C901) FIXME: simply this
    def create_refund_lines(self, order, supplier, created_by, refund_data):
        context = self.get_context_from_order_source(order)

        lines = order.lines.all()
        if supplier:
            lines = lines.filter(supplier=supplier)

        index = lines.aggregate(models.Max("ordering"))["ordering__max"]
        tax_proportions = self._get_tax_class_proportions(order)

        refund_lines = []

        product_summary = order.get_product_summary(supplier)
        available_for_refund = order.get_total_unrefunded_amount(supplier=supplier)
        zero = Money(0, order.currency)
        total_refund_amount = zero

        for refund in refund_data:
            index += 1
            amount = refund.get("amount", zero)
            quantity = refund.get("quantity", 0)
            parent_line = refund.get("line", "amount")
            if not settings.SHUUP_ALLOW_ARBITRARY_REFUNDS and (not parent_line or parent_line == "amount"):
                raise RefundArbitraryRefundsNotAllowedException

            restock_products = refund.get("restock_products")
            refund_line = None

            assert parent_line
            assert quantity

            if parent_line == "amount":
                refund_line = self._refund_amount(
                    context,
                    order,
                    index,
                    refund.get("text", _("Misc refund")),
                    amount,
                    tax_proportions,
                    supplier=supplier,
                )
            else:
                # ensure the amount to refund and the order line amount have the same signs
                if (amount > zero and parent_line.taxful_price.amount < zero) or (
                    amount < zero and parent_line.taxful_price.amount > zero
                ):
                    raise InvalidRefundAmountException

                if abs(amount) > abs(parent_line.max_refundable_amount):
                    raise RefundExceedsAmountException

                # If restocking products, calculate quantity of products to restock
                product = parent_line.product

                # ensure max refundable quantity is respected for products
                if product and quantity > parent_line.max_refundable_quantity:
                    raise RefundExceedsQuantityException

                if restock_products and quantity and product:
                    from shuup.core.suppliers.enums import StockAdjustmentType

                    # restock from the unshipped quantity first
                    unshipped_quantity_to_restock = min(quantity, product_summary[product.pk]["unshipped"])
                    shipped_quantity_to_restock = min(
                        quantity - unshipped_quantity_to_restock,
                        product_summary[product.pk]["ordered"] - product_summary[product.pk]["refunded"],
                    )

                    if unshipped_quantity_to_restock > 0:
                        product_summary[product.pk]["unshipped"] -= unshipped_quantity_to_restock
                        if parent_line.supplier.stock_managed:
                            parent_line.supplier.adjust_stock(
                                product.id,
                                unshipped_quantity_to_restock,
                                created_by=created_by,
                                type=StockAdjustmentType.RESTOCK_LOGICAL,
                            )
                    if shipped_quantity_to_restock > 0 and parent_line.supplier.stock_managed:
                        parent_line.supplier.adjust_stock(
                            product.id,
                            shipped_quantity_to_restock,
                            created_by=created_by,
                            type=StockAdjustmentType.RESTOCK,
                        )
                    product_summary[product.pk]["refunded"] += quantity

                base_amount = amount if order.prices_include_tax else amount / (1 + parent_line.tax_rate)

                from shuup.core.models import OrderLine, OrderLineType

                refund_line = OrderLine.objects.create(
                    text=_("Refund for %s" % parent_line.text),
                    order=order,
                    type=OrderLineType.REFUND,
                    parent_line=parent_line,
                    ordering=index,
                    base_unit_price_value=-(base_amount / (quantity or 1)),
                    quantity=quantity,
                    supplier=parent_line.supplier,
                )
                for line_tax in parent_line.taxes.all():
                    tax_base_amount = amount / (1 + parent_line.tax_rate)
                    tax_amount = tax_base_amount * line_tax.tax.rate
                    refund_line.taxes.create(
                        tax=line_tax.tax,
                        name=_("Refund for %s" % line_tax.name),
                        amount_value=-tax_amount,
                        base_amount_value=-tax_base_amount,
                        ordering=line_tax.ordering,
                    )

            total_refund_amount += refund_line.taxful_price.amount
            refund_lines.append(refund_line)

        if abs(total_refund_amount) > available_for_refund:
            raise RefundExceedsAmountException

        return refund_lines
