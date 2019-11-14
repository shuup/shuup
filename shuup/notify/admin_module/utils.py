# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.apps.provides import get_provide_objects
from shuup.utils.django_compat import force_text


def get_name_map(category_key):
    return sorted([
        (force_text(obj.identifier), force_text(obj.name)) for obj
        in get_provide_objects(category_key)
        if obj.identifier
    ], key=lambda t: t[1].lower())


def get_enum_choices_dict(enum_class):
    return dict(
        (force_text(op.value), force_text(getattr(op, 'label', op.name)))
        for op
        in enum_class
    )
