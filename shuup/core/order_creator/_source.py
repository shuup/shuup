# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import Counter

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum
from six import iteritems

from shuup.core import taxing
from shuup.core.fields.utils import ensure_decimal_places
from shuup.core.models import (
    AnonymousContact, OrderStatus, PaymentMethod, Product, ProductMode,
    ShippingMethod, ShippingMode, Shop, Supplier, TaxClass
)
from shuup.core.pricing import Price, Priceful, TaxfulPrice, TaxlessPrice
from shuup.core.taxing import should_calculate_taxes_automatically, TaxableItem
from shuup.core.utils.line_unit_mixin import LineWithUnit
from shuup.utils.decorators import non_reentrant
from shuup.utils.django_compat import force_text
from shuup.utils.i18n import is_existing_language
from shuup.utils.money import Money

from ._source_modifier import get_order_source_modifier_modules
from .signals import post_compute_source_lines


class OrderLineBehavior(Enum):
    INHERIT = 1  # Inherits the quantity of the parent line if parent exists
    SKIP = 2  # Skips quantity change upon parent line quantity change
    DELETE = 3  # Removes the line upon parent line quantity change

    class Labels:
        INHERIT = _("inherit")
        SKIP = _("skip")
        DELETE = _("delete")


class TaxesNotCalculated(TypeError):
    """
    Requested tax calculated price, but taxes are not calculated.

    Raised when requesting a price with taxful/taxless mismatching with
    `shop.prices_include_tax`, but taxes are not yet calculated.
    """


class _PriceSum(object):
    """
    Property that calculates a sum of prices.

    Used to implement various total price properties to `OrderSource`.

    Calculate the totals same way as for orders which is from rounded
    line prices.
    """

    def __init__(self, field, line_getter="get_final_lines"):
        self.field = field
        self.line_getter = line_getter
        self.params = {}
        if 'taxful' in self.field:
            self.params['includes_tax'] = True
        elif 'taxless' in self.field:
            self.params['includes_tax'] = False

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        taxful = self.params.get('includes_tax', instance.prices_include_tax)
        zero = (TaxfulPrice if taxful else TaxlessPrice)(0, instance.currency)
        lines = getattr(instance, self.line_getter)()
        return sum([getattr(x, self.field) for x in lines], zero)

    @property
    def or_none(self):
        return _UnknownTaxesAsNone(self)


class _UnknownTaxesAsNone(object):
    """
    Property that turns `TaxesNotCalculated` exception to None.

    Used to implement the `OrderSource` taxful/taxless total price
    properties with the "_or_none" suffix.
    """

    def __init__(self, prop):
        self.prop = prop

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        try:
            return self.prop.__get__(instance)
        except TaxesNotCalculated:
            return None


def count_in_line(line):
    truncated_qty = int(line.quantity)
    if not line.unit.allow_bare_number or truncated_qty != line.quantity:
        return 1  # Non-countables or non-integral values counted as 1
    return truncated_qty


class OrderSource(object):
    """
    A "provisional order" object.

    Contains data that is not strictly about a basket's contents,
    but is useful for things that need to calculate something based on the
    basket's contents and extra data, such as shipping/billing addresses.

    The core API of `OrderCreator` reads an `OrderSource`.

    No objects held here need to be saved, but they may be.

    :type shop: shuup.core.models.Shop
    """

    def __init__(self, shop):
        assert isinstance(shop, Shop)
        self.shop = shop
        self.currency = shop.currency
        self.prices_include_tax = shop.prices_include_tax
        self.display_currency = shop.currency
        self.display_currency_rate = 1
        self.shipping_address = None
        self.billing_address = None
        self._customer = None
        self._orderer = None
        self._creator = None
        self._modified_by = None
        self.shipping_method_id = None
        self.payment_method_id = None
        self.customer_comment = u""
        self.marketing_permission = False
        self.ip_address = None  # type: str
        self.order_date = now()
        self.status_id = None
        self.payment_data = {}
        self.shipping_data = {}
        self.extra_data = {}
        self._language = None

        self._codes = []
        self._lines = []

        self.zero_price = shop.create_price(0)
        self.create_price = self.zero_price.new

        self.uncache()  # Initialize caching variables

    def update(self, **values):
        for key, value in values.items():
            if not hasattr(self, key):
                raise ValueError(
                    "Error! Can't update `%r` with key `%r`, as it is not a pre-existing attribute."
                    % (self, key)
                )
            if isinstance(getattr(self, key), dict) and value:  # (Shallowly) merge dicts
                getattr(self, key).update(value)
            else:
                setattr(self, key, value)

    def update_from_order(self, order):
        return self.update(
            shop=order.shop,
            currency=order.currency,
            prices_include_tax=order.prices_include_tax,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            customer=order.customer,
            orderer=order.orderer,
            creator=order.creator,
            modified_by=order.modified_by,
            payment_method_id=order.payment_method_id,
            shipping_method_id=order.shipping_method_id,
            customer_comment=(order.customer_comment if order.customer_comment else ""),
            marketing_permission=order.marketing_permission,
            language=order.language,
            display_currency=order.display_currency,
            display_currency_rate=order.display_currency_rate,
            ip_address=order.ip_address,
            order_date=order.order_date,
            status_id=order.status_id,
            payment_data=order.payment_data,
            shipping_data=order.shipping_data,
            extra_data=order.extra_data,
            codes=order.codes
        )

    total_price = _PriceSum("price")
    taxful_total_price = _PriceSum("taxful_price")
    taxless_total_price = _PriceSum("taxless_price")
    taxful_total_price_or_none = taxful_total_price.or_none
    taxless_total_price_or_none = taxless_total_price.or_none

    total_discount = _PriceSum("discount_amount")
    taxful_total_discount = _PriceSum("taxful_discount_amount")
    taxless_total_discount = _PriceSum("taxless_discount_amount")
    taxful_total_discount_or_none = taxful_total_discount.or_none
    taxless_total_discount_or_none = taxless_total_discount.or_none

    total_price_of_products = _PriceSum("price", "get_product_lines")
    taxful_total_price_of_products = _PriceSum("taxful_price", "get_product_lines")
    taxless_total_price_of_products = _PriceSum("taxless_price", "get_product_lines")

    @property
    def customer(self):
        return (self._customer or AnonymousContact())

    @customer.setter
    def customer(self, value):
        self._customer = value

    @property
    def orderer(self):
        return (self._orderer or AnonymousContact())

    @orderer.setter
    def orderer(self, value):
        self._orderer = value

    @property
    def creator(self):
        return (self._creator or AnonymousUser())

    @creator.setter
    def creator(self, value):
        self._creator = value

    @property
    def modified_by(self):
        return (self._modified_by or self.creator)

    @modified_by.setter
    def modified_by(self, value):
        self._modified_by = value

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

    @property
    def language(self):
        lang = settings.LANGUAGE_CODE
        if self._language:
            lang = self._language
        elif self.customer:
            lang = self.customer.language

        if not is_existing_language(lang):
            lang = settings.LANGUAGE_CODE  # sane fallback

        return lang

    @language.setter
    def language(self, value):
        if not is_existing_language(value):
            value = settings.LANGUAGE_CODE  # sane fallback
        self._language = value

    @status.setter
    def status(self, status):
        self.status_id = (status.id if status else None)

    @property
    def is_empty(self):
        return not bool(self.get_lines())

    @property
    def product_ids(self):
        return set(x.product.id for x in self.get_lines() if x.product)

    def has_shippable_lines(self):
        for line in self.get_lines():
            if line.product:
                if line.product.shipping_mode == ShippingMode.SHIPPED:
                    return True
        return False

    @property
    def codes(self):
        return list(self._codes)

    @codes.setter
    def codes(self, value):
        for code in value:
            self.add_code(code)

    def add_code(self, code):
        """
        Add a code to this OrderSource.

        At this point it is expected that the customers
        permission to use the code has already been
        checked by the caller.

        The code will be converted to text.

        :param code: The code to add.
        :type code: str
        :return: True if code was added, False if it was already there.
        :rtype: bool
        """
        code_text = force_text(code)
        if code_text.upper() not in [c.upper() for c in self._codes]:
            self._codes.append(code_text)
            self.uncache()
            return True
        return False

    def clear_codes(self):
        """
        Remove all codes from this OrderSource.

        :return: True if there were any codes before clearing.
        :rtype: bool
        """
        if self._codes:
            self._codes = []
            self.uncache()
            return True
        return False

    def remove_code(self, code):
        """
        Remove a given code from this OrderSource.

        :param code: The code to remove.
        :type code: str
        :return: True if code was removed, False if code was not there.
        :rtype: bool
        """
        code_text = force_text(code)
        if code_text in self._codes:
            self._codes.remove(code_text)
            self.uncache()
            return True
        return False

    def add_line(self, **kwargs):
        line = self.create_line(**kwargs)
        self._lines.append(line)
        self.uncache()
        return line

    def create_line(self, **kwargs):
        return SourceLine(source=self, **kwargs)

    def get_lines(self):
        """
        Get unprocessed lines in this OrderSource.

        See also `get_final_lines`.
        """
        return self._lines

    @property
    def product_count(self):
        """
        Get the sum of product quantities in this order source.

        Note: It is a bit silly to sum different units together. Check
        `smart_product_count` and `product_line_count` for other
        options.

        :rtype: decimal.Decimal
        """
        return sum([line.quantity for line in self.get_product_lines()])

    @property
    def smart_product_count(self):
        """
        Get the total number of separate products in this order source.

        Quantities of lines, which have countable products, will be
        summed and then number of lines with non-countable product units
        will be added to that. E.g. smart product count for a basket
        containing 5 chocolate bars, 2 t-shirts and 2.5 kg of cocoa beans
        would be 5 + 2 + 1 = 8.

        Definition of "countable" here: If product has an unit that
        allows presenting its quantities as a bare number (see
        `~shuup.core.models.UnitInteface.allow_bare_number`) and its
        quantity is an integral number, we assume that the unit is
        similar to "Pieces" unit and those products being countable.
        Other units are assumed to be non-countable.

        :rtype: int
        """
        return sum(count_in_line(line) for line in self.get_product_lines())

    def count_products(self, supplier=None):
        """
        The same as `smart_product_count``, but accepts a supplier as a filter.

        :rtype: int
        """
        if supplier:
            return sum(count_in_line(line) for line in self.get_product_lines() if line.supplier == supplier)
        return sum(count_in_line(line) for line in self.get_product_lines())

    @property
    def product_line_count(self):
        """
        Get the total number of product lines in this order source.

        :rtype: int
        """
        return len(self.get_product_lines())

    def get_final_lines(self, with_taxes=False):
        """
        Get lines with processed lines added.

        This implementation includes all lines returned by
        `get_lines`. In addition, lines from shipping and payment methods are
        also returned. These latter lines can be extended, deleted or replaced by
        a subclass (by overriding `_compute_processed_lines` method) and
        with the `post_compute_source_lines` signal. Lines returned are not
        validated.

        .. note::

           By default, taxes for the returned lines are not calculated
           when `self.calculate_taxes_automatically` is false. Pass in
           ``True`` to `with_taxes` argument or use `calculate_taxes`
           method to force tax calculation.
        """

        lines = self._processed_lines_cache
        if lines is None:
            lines = self.__compute_lines()
            self._processed_lines_cache = lines
        if not self._taxes_calculated:
            if with_taxes or should_calculate_taxes_automatically():
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
            if not should_calculate_taxes_automatically():
                raise TaxesNotCalculated('Error! Taxes are not calculated.')
            self.calculate_taxes()

    def uncache(self):
        """
        Uncache processed lines.

        Should be called after changing the contents and before
        (re)accessing lines with :obj:`get_final_lines`.
        """
        self._processed_lines_cache = None
        self._taxes_calculated = False
        self._object_cache = {}

    @non_reentrant
    def __compute_lines(self):
        return self._compute_processed_lines()

    def _compute_processed_lines(self):
        # This function would be a good candidate for a subclass extension.
        lines = list(self.get_lines())

        lines.extend(self._compute_payment_method_lines())
        lines.extend(self._compute_shipping_method_lines())
        self._add_lines_from_modifiers(lines)

        lines.extend(_collect_lines_from_signal(
            post_compute_source_lines.send(
                sender=type(self), source=self, lines=lines)))

        return lines

    def _compute_payment_method_lines(self):
        if self.payment_method:
            for line in self.payment_method.get_lines(self):
                yield line

    def _compute_shipping_method_lines(self):
        if self.shipping_method:
            for line in self.shipping_method.get_lines(self):
                yield line

    def _add_lines_from_modifiers(self, lines):
        """
        Add lines from OrderSourceModifiers to a given list of lines.
        """
        for module in get_order_source_modifier_modules():
            new_lines = list(module.get_new_lines(self, list(lines)))
            # Now extend lines to allow the next module to see them.
            lines.extend(new_lines)

    def get_product_lines(self):
        """
        Get lines with a product.

        This does not use `get_final_lines` because it will be called when
        final lines are being computed (for example to determine shipping
        discounts based on the total price of all products).
        """
        product_lines = [line for line in self.get_lines() if line.product]
        return product_lines

    def verify_orderability(self):
        for error_message in self.get_validation_errors():
            raise ValidationError(error_message.args[0], code="invalid_order_source")

    def get_validation_errors(self):  # noqa (C901)
        from shuup.apps.provides import get_provide_objects
        for order_source_validator in get_provide_objects("order_source_validator"):
            for error in order_source_validator.get_validation_errors(self):
                yield error

    def _get_suppliers(self):
        return set([line.supplier for line in self.get_lines() if line.supplier])

    def _get_products_and_quantities(self, supplier=None):
        q_counter = Counter()

        for line in self.get_lines():
            if not line.product:
                continue

            if supplier and line.supplier != supplier:
                continue

            package_children = line.product.get_package_child_to_quantity_map()

            # multiply the quantity by the number os packages in the line
            package_quantity = (int(line.quantity) if line.product.mode == ProductMode.PACKAGE_PARENT else 1)

            for product, quantity in iteritems(package_children):
                q_counter[product] += (quantity * package_quantity)

            product = line.product
            q_counter[product] += line.quantity

        return dict(q_counter)

    @property
    def total_gross_weight(self):
        product_lines = self.get_product_lines()
        return ((sum(line.product.gross_weight * line.quantity for line in product_lines)) if product_lines else 0)

    def _get_object(self, model, pk):
        """
        Get model object from database by pk with caching.

        Avoids the same objects being loaded many times from the database
        when constructing SourceLines in the same request.

        :type model: type
        :type pk: int|Any
        :rtype: django.db.models.Model
        """
        obj = self._object_cache.get((model, pk))
        if not obj:
            obj = model.objects.get(pk=pk)
            self._object_cache[(model, pk)] = obj
        return obj

    def get_total_tax_amount(self):
        """
        :rtype: Money
        """
        return sum(
            (line.tax_amount for line in self.get_final_lines()),
            self.zero_price.amount)

    def get_tax_summary(self):
        """
        :rtype: TaxSummary
        """
        all_line_taxes = []
        untaxed = TaxlessPrice(self.create_price(0).amount)

        for line in self.get_final_lines():
            if line.source != self:
                continue

            line_taxes = list(line.taxes)
            all_line_taxes.extend(line_taxes)
            if not line_taxes:
                untaxed += line.taxless_price
        return taxing.TaxSummary.from_line_taxes(all_line_taxes, untaxed)


def _collect_lines_from_signal(signal_results):
    for (receiver, response) in signal_results:
        for line in response:
            if isinstance(line, SourceLine):
                yield line


class LineSource(Enum):
    CUSTOMER = 1
    SELLER = 2
    ADMIN = 3
    DISCOUNT_MODULE = 4


class SourceLine(TaxableItem, Priceful, LineWithUnit):
    """
    Line of OrderSource.

    Note: Properties like price, taxful_price, tax_rate, etc. are
    inherited from the `Priceful` mixin.
    """
    quantity = None  # override property from Priceful
    base_unit_price = None  # override property from Priceful
    discount_amount = None  # override property from Priceful
    on_parent_change_behavior = OrderLineBehavior.INHERIT

    _FIELDS = [
        "line_id", "parent_line_id", "type",
        "shop", "product", "supplier", "tax_class",
        "quantity", "base_unit_price", "discount_amount",
        "sku", "text",
        "require_verification", "accounting_identifier", "on_parent_change_behavior"
    ]
    _FIELDSET = set(_FIELDS)
    _OBJECT_FIELDS = {
        "shop": Shop,
        "product": Product,
        "supplier": Supplier,
        "tax_class": TaxClass,
    }
    _PRICE_FIELDS = set(["base_unit_price", "discount_amount"])

    def __init__(self, source, **kwargs):
        """
        Initialize SourceLine with a given source and data.

        :param source: The `OrderSource` this `SourceLine` belongs to.
        :type source: OrderSource
        :param kwargs: Data for the `SourceLine`.
        """
        assert isinstance(source, OrderSource)
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
        self.base_unit_price = ensure_decimal_places(kwargs.pop("base_unit_price", source.zero_price))
        self.discount_amount = ensure_decimal_places(kwargs.pop("discount_amount", source.zero_price))
        self.sku = kwargs.pop("sku", "")
        self.text = kwargs.pop("text", "")
        self.require_verification = kwargs.pop("require_verification", False)
        self.accounting_identifier = kwargs.pop("accounting_identifier", "")
        self.on_parent_change_behavior = kwargs.pop("on_parent_change_behavior", OrderLineBehavior.INHERIT)
        self.line_source = kwargs.pop("line_source", LineSource.CUSTOMER)

        self._taxes = None

        self._data = kwargs.copy()

        self._state_check()

    def _state_check(self):
        if not self.base_unit_price.unit_matches_with(self.discount_amount):
            raise TypeError('Error! Unit price %r unit mismatch with discount %r.' % (
                self.base_unit_price, self.discount_amount))

        assert self.shop is None or isinstance(self.shop, Shop)
        assert self.product is None or isinstance(self.product, Product)
        assert self.supplier is None or isinstance(self.supplier, Supplier)

    @classmethod
    def from_dict(cls, source, data):
        """
        Create SourceLine from a given OrderSource and dict.

        :type source: OrderSource
        :type data: dict
        :rtype: cls
        """
        return cls(source, **cls._deserialize_data(source, data))

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
                "Error! You may not add these keys to SourceLine: `%s`." % forbidden_keys)

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
        return self.data.get(key, default)

    @property
    def data(self):
        return self._data or {}

    @property
    def parent_line(self):
        if not self.parent_line_id:
            return None
        for line in self.source.get_lines():
            if line.line_id == self.parent_line_id:
                return line
        raise ValueError('Error! Invalid `parent_line_id`: `%r`.' % (self.parent_line_id,))

    @property
    def tax_class(self):
        return self.product.tax_class if self.product else self._tax_class

    @tax_class.setter
    def tax_class(self, value):
        if self.product and value and value != self.product.tax_class:
            raise ValueError(
                "Error! Conflicting product and line tax classes: `%r` vs. `%r`." % (
                    self.product.tax_class, value))
        self._tax_class = value

    @property
    def taxes(self):
        """
        Taxes of this line.

        Determined by a TaxModule in :func:`OrderSource.calculate_taxes`.

        :rtype: list[shuup.core.taxing.LineTax]
        """
        return self._taxes or []

    @taxes.setter
    def taxes(self, value):
        assert isinstance(value, list)
        assert all(isinstance(x, taxing.LineTax) for x in value)
        self._taxes = value

    @property
    def tax_amount(self):
        """
        :rtype: shuup.utils.money.Money
        """
        self.source.calculate_taxes_or_raise()
        zero = self.source.zero_price.amount
        taxes = self._taxes
        if taxes is None:
            # Taxes were calculated to a different line instance.  Get
            # taxes from there.
            for line in self.source.get_final_lines():
                if line.line_id == self.line_id and line.price == self.price:
                    taxes = line.taxes
        return sum((ensure_decimal_places(x.amount) for x in taxes), zero)

    def _serialize_field(self, key):
        value = getattr(self, key)
        if key in self._OBJECT_FIELDS:
            if value is None:
                return []
            assert isinstance(value, self._OBJECT_FIELDS[key])
            return [(key + "_id", value.id)]
        elif isinstance(value, Price):
            if key not in self._PRICE_FIELDS:
                raise TypeError('Error! Non-price field `%s` has `%r`.' % (key, value))
            if not value.unit_matches_with(self.source.zero_price):
                raise TypeError(
                    'Error! Price `%r` (in field `%s`) not compatible with `%r`.' % (
                        value, key, self.source.zero_price))
            return [(key, value.value)]
        assert not isinstance(value, Money)
        return [(key, value)]

    @classmethod
    def _deserialize_data(cls, source, data):
        result = data.copy()
        for (name, model) in cls._OBJECT_FIELDS.items():
            id = result.pop(name + "_id", None)
            if id:
                result[name] = source._get_object(model, id)

        for name in cls._PRICE_FIELDS:
            value = result.get(name)
            if value is not None:
                result[name] = source.create_price(value)

        return result
