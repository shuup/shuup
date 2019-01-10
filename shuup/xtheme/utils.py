# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.forms.utils import flatatt


def join_css_classes(class_list):
    """
    Join an iterable of truthy values by spaces, effectively creating a list of CSS classes.

    The retval is sorted for cleanliness.

    :param class_list: Iterable of classes
    :type class_list: Iterable[str]
    :return: String
    :rtype: str
    """
    return " ".join(sorted(str(val) for val in class_list if val))


def get_html_attrs(attrs):
    """
    Flatten a dict into HTML attributes (it's `django.forms.utils.flatatt` on steroids!).

    Only truthy keys and values are taken into account; list-like values are flattened
    with `join_css_classes`

    :param attrs: Attribute dict
    :type attrs: dict[str, object]
    :return: string ready to paste after a HTML tag open. `<foo%s>`!
    :rtype: str
    """

    def _massage_attribute(value):
        if isinstance(value, (list, tuple)):
            return join_css_classes(value)
        return value

    attrs = dict(
        (key, _massage_attribute(value))
        for (key, value)
        in six.iteritems(attrs)
        if key and value
    )
    return flatatt(attrs)
