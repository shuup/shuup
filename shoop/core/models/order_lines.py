# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField

from shoop.core.fields import MoneyField, QuantityField, UnsavedForeignKey
from shoop.core.pricing import Price, TaxfulPrice, TaxlessPrice
from shoop.core.taxing import LineTax
from shoop.core.utils.prices import LinePriceMixin

from ._base import ShoopModel


class OrderLineType(Enum):
    PRODUCT = 1
    SHIPPING = 2
    PAYMENT = 3
    CAMPAIGN = 4
    OTHER = 5

    class Labels:
        PRODUCT = _('product')
        SHIPPING = _('shipping')
        PAYMENT = _('payment')
        CAMPAIGN = _('campaign')
        OTHER = _('other')


class OrderLineManager(models.Manager):

    def products(self):  # pragma: no cover
        return self.filter(type=OrderLineType.PRODUCT)

    def shipping(self):  # pragma: no cover
        return self.filter(type=OrderLineType.SHIPPING)

    def payment(self):  # pragma: no cover
        return self.filter(type=OrderLineType.PAYMENT)

    def campaigns(self):  # pragma: no cover
        return self.filter(type=OrderLineType.CAMPAIGN)

    def other(self):  # pragma: no cover
        return self.filter(type=OrderLineType.OTHER)


@python_2_unicode_compatible
class OrderLine(models.Model, LinePriceMixin):
    order = UnsavedForeignKey("Order", related_name='lines', on_delete=models.PROTECT, verbose_name=_('order'))
    product = UnsavedForeignKey(
        "Product", blank=True, null=True, related_name="order_lines",
        on_delete=models.PROTECT, verbose_name=_('product')
    )
    supplier = UnsavedForeignKey(
        "Supplier", blank=True, null=True, related_name="order_lines",
        on_delete=models.PROTECT, verbose_name=_('supplier')
    )

    parent_line = UnsavedForeignKey(
        "self", related_name="child_lines", blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('parent line')
    )
    ordering = models.IntegerField(default=0, verbose_name=_('ordering'))
    type = EnumIntegerField(OrderLineType, default=OrderLineType.PRODUCT, verbose_name=_('line type'))
    sku = models.CharField(max_length=48, blank=True, verbose_name=_('line SKU'))
    text = models.CharField(max_length=256, verbose_name=_('line text'))
    accounting_identifier = models.CharField(max_length=32, blank=True, verbose_name=_('accounting identifier'))
    require_verification = models.BooleanField(default=False, verbose_name=_('require verification'))
    verified = models.BooleanField(default=False, verbose_name=_('verified'))
    extra_data = JSONField(blank=True, null=True)

    # The following fields govern calculation of the prices
    quantity = QuantityField(verbose_name=_('quantity'), default=1)
    _unit_price_amount = MoneyField(verbose_name=_('unit price amount'), default=0)
    _total_discount_amount = MoneyField(verbose_name=_('total amount of discount'), default=0)
    _prices_include_tax = models.BooleanField(default=True)

    objects = OrderLineManager()

    class Meta:
        verbose_name = _('order line')
        verbose_name_plural = _('order lines')

    def __str__(self):
        return "%dx %s (%s)" % (self.quantity, self.text, self.get_type_display())

    @property
    def unit_price(self):
        """
        Unit price of OrderLine.

        :rtype: Price
        """
        if self._prices_include_tax:
            return TaxfulPrice(self._unit_price_amount)
        else:
            return TaxlessPrice(self._unit_price_amount)

    @unit_price.setter
    def unit_price(self, price):
        """
        Set unit price of OrderLine.

        :type price: TaxfulPrice|TaxlessPrice
        """
        self._check_input_price(price)
        self._unit_price_amount = price.amount
        self._prices_include_tax = price.includes_tax

    @property
    def total_discount(self):
        """
        Total discount of OrderLine.

        :rtype: Price
        """
        if self._prices_include_tax:
            return TaxfulPrice(self._total_discount_amount)
        else:
            return TaxlessPrice(self._total_discount_amount)

    @total_discount.setter
    def total_discount(self, discount):
        """
        Set total discount of OrderLine.

        :type discount: TaxfulPrice|TaxlessPrice
        """
        self._check_input_price(discount)
        self._total_discount_amount = discount.amount
        self._prices_include_tax = discount.includes_tax

    @property
    def total_tax_amount(self):
        """
        :rtype: decimal.Decimal
        """
        return sum((x.amount for x in self.taxes.all()), decimal.Decimal(0))

    def _check_input_price(self, price):
        if not isinstance(price, Price):
            raise TypeError('%r is not a Price object' % (price,))
        if self._unit_price_amount or self._total_discount_amount:
            if price.includes_tax != self._prices_include_tax:
                tp = TaxfulPrice if self._prices_include_tax else TaxlessPrice
                msg = 'Cannot accept %r because we want a %s'
                raise TypeError(msg % (price, tp.__name__))

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = u""
        if self.type == OrderLineType.PRODUCT and not self.product_id:
            raise ValidationError("Product-type order line can not be saved without a set product")

        if self.product_id and self.type != OrderLineType.PRODUCT:
            raise ValidationError("Order line has product but is not of Product type")

        if self.product_id and not self.supplier_id:
            raise ValidationError("Order line has product but no supplier")

        return super(OrderLine, self).save(*args, **kwargs)


@python_2_unicode_compatible
class OrderLineTax(ShoopModel, LineTax):
    order_line = models.ForeignKey(
        OrderLine, related_name='taxes', on_delete=models.PROTECT,
        verbose_name=_('order line'))
    tax = models.ForeignKey(  # TODO: (TAX) Should we allow NULL? When deciding, see get_tax_summary
        "Tax", related_name="order_line_taxes",
        on_delete=models.PROTECT, verbose_name=_('tax')
    )
    name = models.CharField(max_length=200, verbose_name=_('tax name'))
    amount = MoneyField(verbose_name=_('tax amount'))
    base_amount = MoneyField(
        verbose_name=_('base amount'),
        help_text=_('Amount that this tax is calculated from'))
    ordering = models.IntegerField(default=0, verbose_name=_('ordering'))

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return "%s: %s on %s" % (self.name, self.amount, self.base_amount)
