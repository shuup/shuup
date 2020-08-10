# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import warnings
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import pgettext
from django.utils.translation import ugettext_lazy as _
from parler.models import (
    TranslatedField, TranslatedFields, TranslatedFieldsModel
)

from shuup.core import cache
from shuup.core.fields import InternalIdentifierField, QuantityField
from shuup.utils.django_compat import force_text
from shuup.utils.i18n import format_number
from shuup.utils.numbers import bankers_round, parse_decimal_string

from ._base import TranslatableShuupModel


# TODO: (2.0) Remove deprecated SalesUnit.short_name
class _ShortNameToSymbol(object):
    def __init__(self, *args, **kwargs):
        if 'short_name' in kwargs:
            self._issue_deprecation_warning()
            kwargs.setdefault('symbol', kwargs.pop('short_name'))
        super(_ShortNameToSymbol, self).__init__(*args, **kwargs)

    @property
    def short_name(self):
        self._issue_deprecation_warning()
        return self.symbol

    @short_name.setter
    def short_name(self, value):
        self._issue_deprecation_warning()
        self.symbol = value

    def _issue_deprecation_warning(self):
        warnings.warn(
            "Warning! `short_name` is deprecated, use `symbol` instead.", DeprecationWarning)


@python_2_unicode_compatible
class SalesUnit(_ShortNameToSymbol, TranslatableShuupModel):
    identifier = InternalIdentifierField(unique=True)
    decimals = models.PositiveSmallIntegerField(default=0, verbose_name=_(u"allowed decimal places"), help_text=_(
        "The number of decimal places allowed by this sales unit."
        "Set this to a value greater than zero if products with this sales unit can be sold in fractional quantities."
    ))

    name = TranslatedField()
    symbol = TranslatedField()

    class Meta:
        verbose_name = _('sales unit')
        verbose_name_plural = _('sales units')

    def __str__(self):
        return force_text(self.safe_translation_getter("name", default=self.identifier) or "")

    @property
    def allow_fractions(self):
        return self.decimals > 0

    @cached_property
    def quantity_step(self):
        """
        Get the quantity increment for the amount of decimals this unit allows.

        For zero decimals, this will be 1; for one decimal, 0.1; etc.

        :return: Decimal in (0..1].
        :rtype: Decimal
        """

        # This particular syntax (`10 ^ -n`) is the same that `bankers_round` uses
        # to figure out the quantizer.

        return Decimal(10) ** (-int(self.decimals))

    def round(self, value):
        return bankers_round(parse_decimal_string(value), self.decimals)

    @property
    def display_unit(self):
        """
        Default display unit of this sales unit.

        Get a `DisplayUnit` object, which has this sales unit as its
        internal unit and is marked as a default, or if there is no
        default display unit for this sales unit, then a proxy object.
        The proxy object has the same display unit interface and mirrors
        the properties of the sales unit, such as symbol and decimals.

        :rtype: DisplayUnit
        """
        cache_key = "display_unit:sales_unit_{}_default_display_unit".format(self.pk)
        default_display_unit = cache.get(cache_key)

        if default_display_unit is None:
            default_display_unit = self.display_units.filter(default=True).first()
            # Set 0 to cache to prevent None values, which will not be a valid cache value
            # 0 will be invalid below, hence we prevent another query here
            cache.set(cache_key, default_display_unit or 0)

        return default_display_unit or SalesUnitAsDisplayUnit(self)


class SalesUnitTranslation(_ShortNameToSymbol, TranslatedFieldsModel):
    master = models.ForeignKey(
        on_delete=models.CASCADE, to=SalesUnit, related_name='translations', null=True, editable=False)
    name = models.CharField(
        max_length=128, verbose_name=_('name'), help_text=_(
            "The sales unit name to use for products (e.g. "
            "'pieces' or 'units'). Sales units can be set individually for each "
            "product through the product editor view."))
    symbol = models.CharField(
        max_length=128, verbose_name=_("unit symbol"), help_text=_(
            "An abbreviated name for this sales unit that is shown "
            "throughout admin and order invoices."))

    class Meta:
        # Use same meta options as Parler's defaults to avoid migration
        unique_together = [('language_code', 'master')]
        verbose_name = "sales unit Translation"
        db_table = SalesUnit._meta.db_table + '_translation'
        db_tablespace = SalesUnit._meta.db_tablespace
        managed = SalesUnit._meta.managed
        default_permissions = ()


def validate_positive_not_zero(value):
    if value <= 0:
        raise ValidationError(_("Value must be positive and non-zero."))


class DisplayUnit(TranslatableShuupModel):
    internal_unit = models.ForeignKey(
        on_delete=models.CASCADE, to=SalesUnit, related_name='display_units',
        verbose_name=_("internal unit"), help_text=_("The sales unit that this display unit is linked to."))
    ratio = QuantityField(
        default=1, validators=[validate_positive_not_zero],
        verbose_name=_("ratio"),
        help_text=_(
            "Size of the display unit in internal unit. E.g. if "
            "internal unit is kilogram and display unit is gram, "
            "ratio is 0.001."))
    decimals = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("decimal places"),
        help_text=_(
            "The number of decimal places to use for values in the "
            "display unit. The internal values are still rounded "
            "based on the settings of the internal unit."))
    comparison_value = QuantityField(
        default=1, validators=[validate_positive_not_zero],
        verbose_name=_("comparison value"),
        help_text=_(
            "Value to use when displaying unit prices. E.g. if the "
            "display unit is a gram and the comparison value is 100, then "
            "unit prices are shown per 100g, like: $2.95 per 100g."))
    allow_bare_number = models.BooleanField(
        default=False, verbose_name=_("allow bare number"),
        help_text=_(
            "If true, values of this unit can occasionally be shown "
            "without the symbol attached to it. E.g. if the unit is a "
            "`piece`, then you might want for the product listings to "
            "only show '$5.95' rather than '$5.95 per pc.'."))
    default = models.BooleanField(
        default=False, verbose_name=_("use by default"), help_text=_(
            "Use this display unit by default when displaying "
            "values of the internal unit."))
    translations = TranslatedFields(
        name=models.CharField(
            max_length=150, verbose_name=_("name"), help_text=_(
                "Name of the display unit, e.g. grams.")),
        symbol=models.CharField(
            max_length=50, verbose_name=_("symbol"), help_text=_(
                "An abbreviated name of the display unit, e.g. 'g'.")),
    )

    class Meta:
        verbose_name = _("display unit")
        verbose_name_plural = _("display units")


@python_2_unicode_compatible
class SalesUnitAsDisplayUnit(DisplayUnit):
    class Meta:
        abstract = True

    def __init__(self, sales_unit):
        super(SalesUnitAsDisplayUnit, self).__init__()
        self.internal_unit = sales_unit
        self.ratio = Decimal(1)
        self.decimals = sales_unit.decimals
        self.comparison_value = Decimal(1)
        self.allow_bare_number = (sales_unit.decimals == 0)
        self.default = False

    def _get_pk_val(self, meta=None):
        return None

    pk = property(_get_pk_val)
    name = property(lambda self: self.internal_unit.name)
    symbol = property(lambda self: self.internal_unit.symbol)

    def __str__(self):
        return force_text(self.name)


@python_2_unicode_compatible
class PiecesSalesUnit(SalesUnit):
    """
    An object representing `Pieces` sales unit.

    Has same API as SalesUnit, but isn't a real model.
    """
    class Meta:
        abstract = True

    def __init__(self):
        super(PiecesSalesUnit, self).__init__(
            identifier='_internal_pieces_unit', decimals=0)

    def _get_pk_val(self, meta=None):
        return None

    pk = property(_get_pk_val)
    name = _("Pieces")
    symbol = pgettext("Symbol for pieces unit", "pc.")

    @property
    def display_unit(self):
        return SalesUnitAsDisplayUnit(self)

    def __str__(self):
        return force_text(self.name)


class UnitInterface(object):
    """
    Interface to unit functions.

    Provides methods for rounding, rendering and converting product
    quantities in display or internal units.
    """
    def __init__(self, internal_unit=None, display_unit=None):
        """
        Initialize unit interface.

        :type internal_unit: SalesUnit
        :type display_unit: DisplayUnit
        """
        assert internal_unit is None or display_unit is None or (
            display_unit.internal_unit == internal_unit), (
                "Incompatible units: %r, %r" % (internal_unit, display_unit))
        if display_unit:
            self.internal_unit = display_unit.internal_unit
            self.display_unit = display_unit
        else:
            self.internal_unit = internal_unit or PiecesSalesUnit()
            self.display_unit = self.internal_unit.display_unit
        assert self.display_unit.internal_unit == self.internal_unit

    @property
    def symbol(self):
        """
        Symbol of the display unit.

        :rtype: str
        """
        return self.display_unit.symbol or PiecesSalesUnit.symbol

    def get_symbol(self, allow_empty=True):
        """
        Returns symbol of the display unit or empty if it is not needed.

        :rtype: str
        """
        if allow_empty and self.allow_bare_number and (
                self.display_unit.comparison_value == 1):
            return ''
        return self.symbol

    @property
    def internal_symbol(self):
        """
        Symbol of the internal unit.

        :rtype: str
        """
        return self.internal_unit.symbol

    @property
    def allow_bare_number(self):
        """
        Allow showing values without the unit symbol.

        :rtype: bool
        """
        return self.display_unit.allow_bare_number

    @property
    def display_precision(self):
        """
        Smallest possible non-zero quantity in the display unit.
        """
        return Decimal('0.1') ** self.display_unit.decimals

    def render_quantity(self, quantity, force_symbol=False):
        """
        Render (internal unit) quantity in the display unit.

        The value is converted from the internal unit to the display
        unit and then localized. The display unit symbol is added if
        needed.

        :type quantity: Decimal
        :param quantity: Quantity to render, in internal unit.
        :type force_symbol: bool
        :param force_symbol: Make sure that the symbol is rendered.
        :rtype: str
        :return: Rendered quantity in display unit.
        """
        display_quantity = self.to_display(quantity)
        value = format_number(display_quantity, self.display_unit.decimals)
        symbol = self.get_symbol(allow_empty=(not force_symbol))
        if not symbol:
            return value
        return _get_value_symbol_template().format(value=value, symbol=symbol)

    def render_quantity_internal(self, quantity, force_symbol=False):
        """
        Render quantity in the internal unit.

        The value is rounded, localized and the internal unit symbol is
        added if needed.

        :type quantity: Decimal
        :param quantity: Quantity to render, in internal unit.
        :type force_symbol: bool
        :param force_symbol: Make sure that the symbol is rendered.
        :rtype: str
        :return: Rendered quantity in internal unit.
        """
        rounded = _round_to_digits(
            Decimal(quantity), self.internal_unit.decimals, ROUND_HALF_UP)
        value = format_number(rounded, self.internal_unit.decimals)
        if not force_symbol and self.allow_bare_number:
            return value
        symbol = self.internal_unit.symbol
        return _get_value_symbol_template().format(value=value, symbol=symbol)

    def to_display(self, quantity, rounding=ROUND_HALF_UP):
        """
        Convert quantity from internal unit to display unit.

        :type quantity: Decimal
        :param quantity: Quantity to convert, in internal unit.
        :rtype: Decimal
        :return: Converted quantity, in display unit.
        """
        value = Decimal(quantity) / self.display_unit.ratio
        return _round_to_digits(value, self.display_unit.decimals, rounding)

    def from_display(self, display_quantity, rounding=ROUND_HALF_UP):
        """
        Convert quantity from display unit to internal unit.

        :type quantity: Decimal
        :param quantity: Quantity to convert, in display unit.
        :rtype: Decimal
        :return: Converted quantity, in internal unit.
        """
        value = Decimal(display_quantity) * self.display_unit.ratio
        return _round_to_digits(value, self.internal_unit.decimals, rounding)

    def get_per_values(self, force_symbol=False):
        """
        Get "per" quantity and "per" text according to the display unit.

        Useful when rendering unit prices, e.g.::

          (per_qty, per_text) = unit.get_per_values(force_symbol=True)
          price = product.get_price(quantity=per_qty)
          unit_price_text = _("{price} per {per_text}").format(
              price=price, per_text=per_text)

        :rtype: (Decimal, str)
        :return:
          Quantity (in internal unit) and text to use as the unit in
          unit prices.
        """
        symbol = self.get_symbol(allow_empty=(not force_symbol))
        without_value = (self.display_unit.comparison_value == 1)
        per_qty = self.comparison_quantity
        per_text = (symbol if without_value else self.render_quantity(per_qty))
        return (per_qty, per_text)

    @property
    def comparison_quantity(self):
        """
        Quantity (in internal units) to use as the unit in unit prices.

        :rtype: Decimal
        :return: Quantity, in internal unit.
        """
        return self.from_display(self.display_unit.comparison_value)


def _get_value_symbol_template():
    return pgettext(
        "Display the value with the unit symbol (with or without space) ",
        "{value}{symbol}")


def _round_to_digits(value, digits, rounding=ROUND_HALF_UP):
    precision = Decimal('1.' + ('1' * digits))
    return value.quantize(precision, rounding=rounding)


def bump_sales_unit_cache_signal(*args, **kwargs):
    cache.bump_version("display_unit")


post_save.connect(bump_sales_unit_cache_signal, sender=SalesUnit)
post_save.connect(bump_sales_unit_cache_signal, sender=DisplayUnit)
