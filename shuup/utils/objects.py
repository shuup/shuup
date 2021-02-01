# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six


def extract_inner_value(source, attr_chain):
    """
    Search for a stored value by recursing through dict keys and attributes.
    Erroneous/missing keys/attribute names will return None.

    :param source: The original object, that either has attributes or is itself a dict.
    :param attr_chain: A tuple of properly ordered strings,
                       containing the attributes and/or keys to successively obtain.
    :type attr_chain: tuple

    >>> mydict = {"foo": {"bar": {"thing": 25}}}
    >>> extract_inner_value(mydict, ("foo", "bar", "thing"))
    25
    >>> extract_inner_value(mydict, ("foo", "bar", "unthing"))
    >>> bool(extract_inner_value(mydict, ("__getitem__",)))
    True
    >>> bool(extract_inner_value(mydict, ("__getotem__",)))
    False
    """

    cur_element = source
    for attr in attr_chain:
        if hasattr(cur_element, "__getitem__"):
            try:
                cur_element = cur_element[attr]
                continue
            except (KeyError, TypeError):
                pass

        cur_element = getattr(cur_element, attr, None)
        if cur_element is None:
            return None
    return cur_element


def compare_partial_dicts(source, comparee):
    """
    Compare dicts in a "partial" manner.
    All key/value pairs in `source` must exist and be equal to those in `comparee`.

    This differs from a raw == in that keys that do not exist in `source` may exist in `comparee`.

    :param source: source dict
    :type source: dict
    :param comparee: comparee dict
    :type comparee: dict
    :rtype: bool
    :return: True or False
    """

    for key, value in six.iteritems(source):
        if key not in comparee or value != comparee[key]:
            return False

    return True


def compact(in_obj, none_only=True, deep=True):
    """
    Compact iterable by removing falsy values.

    Iterable may be a mapping or a list.

    By default uses ``not value`` to test for falseness, but if
    `none_only` is set, will use ``value is None``.

    By default, iterables within the iterable are also compacted.  This
    can be controlled by the `deep` argument.

    :param in_obj: The object to compact
    :type in_obj: Iterable
    :param none_only: Remove only Nones
    :type none_only: bool
    :param deep: Recurse through iterables within `in_obj`
    :type deep: bool
    :return: Flattened iterable
    :rtype: list|dict
    """

    if isinstance(in_obj, dict) or hasattr(in_obj, "keys"):
        is_dict = True
        iterator = six.iteritems(in_obj)
        out_obj = {}
    else:
        is_dict = False
        iterator = enumerate(in_obj)
        out_obj = []

    for key, value in iterator:
        if none_only and value is None:
            continue
        if not value:
            continue
        if deep and hasattr(value, "__iter__") and not isinstance(value, six.string_types):
            value = compact(value, none_only=none_only, deep=True)
        if is_dict:
            out_obj[key] = value
        else:
            out_obj.append(value)
    return out_obj
