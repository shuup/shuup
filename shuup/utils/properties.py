# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.core.pricing import Price, TaxfulPrice, TaxlessPrice
from shuup.utils.money import Money
from shuup.utils.numbers import UnitMixupError


class MoneyProperty(object):
    """
    Property for a Money amount.

    Will return `Money` objects when the property is being get and
    accepts `Money` objects on set.  Value and currency are read/written
    from/to other fields.

    Fields are given as locators, that is a string in dotted format,
    e.g. locator ``"foo.bar"`` points to ``instance.foo.bar`` where
    ``instance`` is an instance of the class owning the `MoneyProperty`.

    Setting value of this property to a `Money` object with different
    currency that is currently set (in the field pointed by the currency
    locator), will raise an `UnitMixupError`.
    """

    value_class = Money

    def __init__(self, value, currency):
        """
        Initialize MoneyProperty with given field locators.

        :param value: Locator for value of the Money.
        :type value: str
        :param currency: Locator for currency of the Money.
        :type currency: str
        """
        self._fields = {"value": value, "currency": currency}

    def __repr__(self):
        argstr = ", ".join("%s=%r" % x for x in self._fields.items())
        return "%s(%s)" % (type(self).__name__, argstr)

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        return self._get_value_from(instance)

    def _get_value_from(self, instance, overrides={}):
        data = {field: resolve(instance, path) for (field, path) in self._fields.items()}
        data.update(overrides)
        if data["value"] is None:
            return None
        return self.value_class.from_data(**data)

    def __set__(self, instance, value):
        if value is not None:
            self._check_unit(instance, value)
        self._set_part(instance, "value", value)

    def _check_unit(self, instance, value):
        value_template = self._get_value_from(instance, overrides={"value": 0})
        if not value_template.unit_matches_with(value):
            msg = "Error! Can't set `%s` to value with non-matching unit." % (type(self).__name__,)
            raise UnitMixupError(value_template, value, msg)
        assert isinstance(value, self.value_class)

    def _set_part(self, instance, part_name, value):
        value_full_path = self._fields[part_name]
        if "." in value_full_path:
            (obj_path, attr_to_set) = value_full_path.rsplit(".", 1)
            obj = resolve(instance, obj_path)
        else:
            attr_to_set = value_full_path
            obj = instance
        if value is not None:
            setattr(obj, attr_to_set, getattr(value, part_name))
        else:
            setattr(obj, attr_to_set, None)


class PriceProperty(MoneyProperty):
    """
    Property for Price object.

    Similar to `MoneyProperty`, but also has ``includes_tax`` field.

    Operaters with `TaxfulPrice` and `TaxlessPrice` objects.
    """

    value_class = Price

    def __init__(self, value, currency, includes_tax, **kwargs):
        """
        Initialize PriceProperty with given field locators.

        :param value: Locator for value of the Price.
        :type value: str
        :param currency: Locator for currency of the Price.
        :type currency: str
        :param includes_tax: Locator for includes_tax of the Price.
        :type includes_tax: str
        """
        super(PriceProperty, self).__init__(value, currency, **kwargs)
        self._fields["includes_tax"] = includes_tax


class TaxfulPriceProperty(MoneyProperty):
    value_class = TaxfulPrice


class TaxlessPriceProperty(MoneyProperty):
    value_class = TaxlessPrice


class MoneyPropped(object):
    """
    Mixin for transforming MoneyProperty init parameters.

    Add this mixin as (first) base for the class that has
    `MoneyProperty` properties and this will make its `__init__`
    transform passed kwargs to the fields specified in the
    `MoneyProperty`.
    """

    def __init__(self, *args, **kwargs):
        transformed = _transform_init_kwargs(type(self), kwargs)
        super(MoneyPropped, self).__init__(*args, **kwargs)
        _check_transformed_types(self, transformed)


def _transform_init_kwargs(cls, kwargs):
    transformed = []
    for field in list(kwargs.keys()):
        prop = getattr(cls, field, None)
        if isinstance(prop, MoneyProperty):
            value = kwargs.pop(field)
            _transform_single_init_kwarg(prop, field, value, kwargs)
            transformed.append((field, value))
    return transformed


def _transform_single_init_kwarg(prop, field, value, kwargs):
    if value is not None and not isinstance(value, prop.value_class):
        raise TypeError(
            "Error! Expecting type `%s` for field `%s` (got `%r`)." % (prop.value_class.__name__, field, value)
        )
    for (attr, path) in prop._fields.items():
        if "." in path:
            continue  # Only set "local" fields
        if path in kwargs:
            f = (field, path)
            raise TypeError("Error! Fields `%s` and `%s` conflict." % f)
        if value is None:
            kwargs[path] = None
        else:
            kwargs[path] = getattr(value, attr)


def _check_transformed_types(self, transformed):
    for (field, orig_value) in transformed:
        new_value = getattr(self, field)
        if new_value != orig_value:
            msg = "Error! Cannot set `%s` to `%r` (try `%r`)."
            raise TypeError(msg % (field, orig_value, new_value))


def resolve(obj, path):
    """
    Resolve a locator `path` starting from object `obj`.
    """
    if path:
        for name in path.split("."):
            obj = getattr(obj, name, None)
    return obj
