# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal

from django.conf import settings
from django.utils.timezone import now

from shoop.core import taxing
from shoop.core.models import OrderStatus, PaymentMethod, Product, ShippingMethod, Shop, Supplier, TaxClass
from shoop.core.pricing import Price, TaxfulPrice, TaxlessPrice
from shoop.core.taxing import TaxableItem
from shoop.core.utils.prices import LinePriceMixin
from shoop.utils.decorators import non_reentrant

from .signals import post_compute_source_lines


class OrderSource(object):
    """
    A "provisional order" object.

    Contains data that's not strictly about a basket's contents,
    but is useful for things that need to calculate something based on the
    basket's contents and extra data, such as shipping/billing addresses.

    The core API of `OrderCreator` reads an `OrderSource`.

    No objects held here need be saved, but they may be.
    """

    def __init__(self):
        self.shop = None
        self.display_currency = settings.SHOOP_HOME_CURRENCY
        self.display_currency_rate = 1
        self.shipping_address = None
        self.billing_address = None
        self.customer = None
        self.orderer = None
        self.creator = None
        self.shipping_method_id = None
        self.payment_method_id = None
        self.customer_comment = u""
        self.marketing_permission = False
        self.language = None
        self.order_date = now()
        self.status_id = None
        self.payment_data = {}
        self.shipping_data = {}
        self.extra_data = {}

        self._lines = []

        # TODO: (TAX) How to set calculate_taxes_automatically? From a setting?
        self.calculate_taxes_automatically = False
        """
        Calculate taxes automatically when lines are added or processed.

        Set to False to minimize costs and latency, since it is possible
        that the current TaxModule implemements tax calculations with an
        integration to a remote system which charges per transaction.
        """

        self._taxes_calculated = False
        self._processed_lines_cache = None

    def update(self, **values):
        for key, value in values.items():
            if not hasattr(self, key):
                raise ValueError("Can't update %r with key %r, it's not a pre-existing attribute" % (self, key))
            if isinstance(getattr(self, key), dict):  # (Shallowly) merge dicts
                getattr(self, key).update(value)
            else:
                setattr(self, key, value)

    def update_from_order(self, order):
        return self.update(
            shop=order.shop,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            customer=order.customer,
            orderer=order.orderer,
            creator=order.creator,
            payment_method_id=order.payment_method_id,
            shipping_method_id=order.shipping_method_id,
            customer_comment=order.customer_comment,
            marketing_permission=order.marketing_permission,
            language=order.language,
            display_currency=order.display_currency,
            display_currency_rate=order.display_currency_rate,
            order_date=order.order_date,
            status_id=order.status_id,
            payment_data=order.payment_data,
            shipping_data=order.shipping_data,
            extra_data=order.extra_data,
        )

    @property
    def shipping_method(self):
        if self.shipping_method_id:
            return ShippingMethod.objects.get(pk=self.shipping_method_id)

    @shipping_method.setter
    def shipping_method(self, shipping_method):
        self.shipping_method_id = (shipping_method.id if shipping_method else None)

    @property
    def payment_method(self):
        if self.payment_method_id:
            return PaymentMethod.objects.get(pk=self.payment_method_id)

    @payment_method.setter
    def payment_method(self, payment_method):
        self.payment_method_id = (payment_method.id if payment_method else None)

    @property
    def status(self):
        if self.status_id:
            return OrderStatus.objects.get(pk=self.status_id)

    @status.setter
    def status(self, status):
        self.status_id = (status.id if status else None)

    def add_line(self, **kwargs):
        line = SourceLine(source=self, **kwargs)
        self._lines.append(line)
        self.uncache()
        return line

    def get_lines(self):
        """
        Get unprocessed lines in this OrderSource.

        See also `get_final_lines`.
        """
        return self._lines

    def get_final_lines(self, with_taxes=False):
        """
        Get lines with processed lines added.

        This implementation includes the all lines returned by
        `get_lines` and in addition, lines from shipping and payment
        methods, but these lines can be extended, deleted or replaced by
        a subclass (by overriding `_compute_processed_lines` method) and
        with the `post_compute_source_lines` signal.

        .. note::

           By default, taxes for the returned lines are not calculated
           when `self.calculate_taxes_automatically` is false.  Pass in
           ``True`` to `with_taxes` argument or use `calculate_taxes`
           method to force tax calculation.
        """

        lines = self._processed_lines_cache
        if lines is None:
            lines = self.__compute_lines()
            self._processed_lines_cache = lines
        if not self._taxes_calculated:
            if with_taxes or self.calculate_taxes_automatically:
                self._calculate_taxes(lines)
        return lines

    def calculate_taxes(self, force_recalculate=False):
        if force_recalculate:
            self._taxes_calculated = False
        self.get_final_lines(with_taxes=True)

    def _calculate_taxes(self, lines):
        tax_module = taxing.get_tax_module()
        tax_module.add_taxes(self, lines)
        self._taxes_calculated = True

    def calculate_taxes_or_raise(self):
        if not self._taxes_calculated:
            if not self.calculate_taxes_automatically:
                raise TaxesNotCalculated('Taxes are not calculated')
            self.calculate_taxes()

    def uncache(self):
        """
        Uncache processed lines.

        Should be called after changing the contents before
        (re)accessing lines with :obj:`get_final_lines`.
        """
        self._processed_lines_cache = None
        self._taxes_calculated = False

    @non_reentrant
    def __compute_lines(self):
        return self._compute_processed_lines()

    def _compute_processed_lines(self):
        # This function would be a good candidate for subclass extension.
        lines = self.get_lines()

        lines.extend(self._compute_payment_method_lines())
        lines.extend(self._compute_shipping_method_lines())

        lines.extend(_collect_lines_from_signal(
            post_compute_source_lines.send(
                sender=type(self), source=self, lines=lines)))

        return lines

    def _compute_payment_method_lines(self):
        if self.payment_method:
            for line in self.payment_method.get_source_lines(self):
                yield line

    def _compute_shipping_method_lines(self):
        if self.shipping_method:
            for line in self.shipping_method.get_source_lines(self):
                yield line

    def prices_include_tax(self):
        # TODO: (TAX) Get taxfulness default from request or PriceTaxContext or customer or whatever
        return False

    @property
    def total_price(self):
        if self.prices_include_tax():
            return self.taxful_total_price
        else:
            return self.taxless_total_price

    @property
    def taxful_total_price(self):
        return sum_taxful_totals(self.get_final_lines())

    @property
    def taxless_total_price(self):
        return sum_taxless_totals(self.get_final_lines())

    @property
    def product_total_price(self):
        if self.prices_include_tax():
            return self.taxful_product_total_price
        else:
            return self.taxless_product_total_price

    @property
    def taxful_product_total_price(self):
        return sum_taxful_totals(self._get_product_lines())

    @property
    def taxless_product_total_price(self):
        return sum_taxless_totals(self._get_product_lines())

    def _get_product_lines(self):
        # This does not use get_final_lines because it will be called
        # when final lines is being computed
        product_lines = [l for l in self.get_lines() if l.product]
        return product_lines

    def get_validation_errors(self):
        shipping_method = self.shipping_method
        payment_method = self.payment_method

        if shipping_method:
            for error in shipping_method.get_validation_errors(source=self):
                yield error

        if payment_method:
            for error in payment_method.get_validation_errors(source=self):
                yield error


def sum_taxful_totals(lines):
    return sum((x.taxful_total_price for x in lines), TaxfulPrice(0))


def sum_taxless_totals(lines):
    return sum((x.taxless_total_price for x in lines), TaxlessPrice(0))


def _collect_lines_from_signal(signal_results):
    for (receiver, response) in signal_results:
        for line in response:
            if isinstance(line, SourceLine):
                yield line


class SourceLine(TaxableItem, LinePriceMixin):
    _FIELDS = [
        "line_id", "parent_line_id", "type",
        "shop", "product", "supplier", "tax_class",
        "quantity", "unit_price", "total_discount",
        "sku", "text",
        "require_verification", "accounting_identifier",
        # TODO: Maybe add following attrs to SourceLine?
        # "weight"
    ]
    _FIELDSET = set(_FIELDS)
    _OBJECT_FIELDS = {
        "shop": Shop,
        "product": Product,
        "supplier": Supplier,
        "tax_class": TaxClass,
    }
    _PRICE_FIELDS = set(["unit_price", "total_discount"])

    def __init__(self, source=None, **kwargs):
        """
        Initialize SourceLine with given source and data.

        :param source: The `OrderSource` this `SourceLine` belongs to.
        :type source: OrderSource
        :param kwargs: Data for the `SourceLine`.
        """
        self.source = source
        self.line_id = kwargs.pop("line_id", None)
        self.parent_line_id = kwargs.pop("parent_line_id", None)
        self.type = kwargs.pop("type", None)
        self.shop = kwargs.pop("shop", None)
        self.product = kwargs.pop("product", None)
        tax_class = kwargs.pop("tax_class", None)
        if not self.product:
            # Only set tax_class when there is no product set, since
            # tax_class property will get the value from the product and
            # setter will fail when trying to set conflicting tax class
            # (happens when tax_class of the Product has changed)
            self.tax_class = tax_class
        self.supplier = kwargs.pop("supplier", None)
        self.quantity = kwargs.pop("quantity", 0)
        self.unit_price = kwargs.pop("unit_price", self._create_price(0))
        self.total_discount = (kwargs.get("total_discount", None) or
                               0 * self.unit_price)
        self.sku = kwargs.pop("sku", "")
        self.text = kwargs.pop("text", "")
        self.require_verification = kwargs.pop("require_verification", False)
        self.accounting_identifier = kwargs.pop("accounting_identifier", "")
        self.taxes = []
        self._data = kwargs.copy()

        self._state_check()

    def _state_check(self):
        if self.unit_price.includes_tax != self.total_discount.includes_tax:
            raise TypeError('Unit price %r tax mismatch with discount %r' % (
                self.unit_price, self.total_discount))

        assert self.shop is None or isinstance(self.shop, Shop)
        assert self.product is None or isinstance(self.product, Product)
        assert self.supplier is None or isinstance(self.supplier, Supplier)

    @classmethod
    def from_dict(cls, source, data):
        """
        Create SourceLine from given OrderSource and dict.

        :type source: OrderSource
        :type data: dict
        :rtype: cls
        """
        return cls(source, **cls._deserialize_data(data))

    def to_dict(self):
        data = self._data.copy()
        for key in self._FIELDS:
            data.update(self._serialize_field(key))
        return data

    def update(self, **kwargs):
        forbidden_keys = set(dir(self)) - self._FIELDSET
        found_forbidden_keys = [key for key in kwargs if key in forbidden_keys]
        if found_forbidden_keys:
            raise TypeError(
                "You may not add these to SourceLine: %s" % forbidden_keys)

        for (key, value) in kwargs.items():
            if key in self._FIELDSET:
                setattr(self, key, value)
            else:
                self._data[key] = value

    def __repr__(self):
        key_values = [(key, getattr(self, key, None)) for key in self._FIELDS]
        set_key_values = [(k, v) for (k, v) in key_values if v is not None]
        assigns = [
            "%s=%r" % (k, v)
            for (k, v) in (set_key_values + sorted(self._data.items()))]
        return "<%s(%r, %s)>" % (
            type(self).__name__, self.source, ", ".join(assigns))

    def get(self, key, default=None):
        if key in self._FIELDSET:
            return getattr(self, key, default)
        return self._data.get(key, default)

    @property
    def tax_class(self):
        return self.product.tax_class if self.product else self._tax_class

    @tax_class.setter
    def tax_class(self, value):
        if self.product and value and value != self.product.tax_class:
            raise ValueError(
                "Conflicting product and line tax classes: %r vs %r" % (
                    self.product.tax_class, value))
        self._tax_class = value

    @property
    def total_tax_amount(self):
        """
        :rtype: decimal.Decimal
        """
        return sum((x.amount for x in self.taxes), decimal.Decimal(0))

    def _create_price(self, amount):
        if self.source and self.source.prices_include_tax():
            return TaxfulPrice(amount)
        else:
            return TaxlessPrice(amount)

    def _serialize_field(self, key):
        value = getattr(self, key)
        if key in self._OBJECT_FIELDS:
            if value is None:
                return []
            assert isinstance(value, self._OBJECT_FIELDS[key])
            return [(key + "_id", value.id)]
        elif key in self._PRICE_FIELDS:
            assert isinstance(value, Price)
            return [
                (key, None),
                (key + "_amount", value.value),
                (key + "_includes_tax", value.includes_tax),
            ]
        return [(key, value)]

    @classmethod
    def _deserialize_data(cls, data):
        result = data.copy()
        for (name, model) in cls._OBJECT_FIELDS.items():
            id = result.pop(name + "_id", None)
            if id:
                result[name] = model.objects.get(id=id)

        for name in cls._PRICE_FIELDS:
            amount = result.pop(name + "_amount", None)
            includes_tax = result.pop(name + "_includes_tax", None)
            if amount is not None:
                result[name] = Price.from_data(amount, None, includes_tax)

        return result
