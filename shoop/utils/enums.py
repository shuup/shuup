# -*- coding: utf-8 -*-
from __future__ import absolute_import
from numbers import Number

import six

RAISE = object()


def map_enum(enum_cls, value, default=RAISE, allow_magic_numbers=False):
    """
    Attempt to cast the given `value` into a value of the given `enum_cls`.

    Tries by value first, then case-insensitively by name.

    If casts fail, the `default` is returned (unless it is the default sentinel
    object `RAISE`, in which case a `ValueError` is raised).

    This is useful for places where it doesn't make sense to export the actual
    enumeration classes (such as into templates, etc.) while still avoiding
    "magic constants" (i.e. the actual enum values).  For the aforementioned
    reason of being used in templates, it is purposefully slightly more
    lenient in its parsing than more "core" utilities might be.

    :param enum_cls: Enum class
    :type enum_cls: enum.Enum
    :param value: value or name
    :type value: object|str
    :param default: Default value to return in case of trouble
    :type default:
    :param allow_magic_numbers: Allow mapping via "magic numbers". If this is False and
                                the value is a number, ValueError is raised.
    :type allow_magic_numbers: bool
    :return: A mapped enum value, or the passed default.
    :rtype: object
    :raises ValueError: ValueError is raised when the value is unmappable.
    """

    # First, try the default logic of enums:

    if not allow_magic_numbers and isinstance(value, Number):
        raise ValueError(
            "The value %r can not be mapped to a %r (magic numbers are not allowed)" % (value, enum_cls)
        )

    try:
        return enum_cls(value)
    except ValueError:
        pass

    # Then, get or create the mapping for case-insensitive name logic.
    # The mapping is stored as a "private" attribute of the enum class.

    members = getattr(enum_cls, "_map_enum_cache_", None)
    if members is None:
        members = dict((k.lower(), v) for (k, v) in enum_cls.__members__.items())
        enum_cls._map_enum_cache_ = members

    # Try looking up the value in the mapping.

    retval = members.get(six.text_type(value).lower(), default)

    if retval is RAISE:
        raise ValueError("Can't map value %r to any member of enum %r" % (value, enum_cls))
    return retval
