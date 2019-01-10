# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps.provides import get_provide_objects


def get_customer_from_context(context):
    request = context.get("request")
    return (request.customer if request else None)


def get_layout_data_key(placeholder_name, layout, context):
    if isinstance(layout, dict):
        return placeholder_name

    data_suffix = layout.get_layout_data_suffix(context)
    if data_suffix:
        return "%s-%s" % (placeholder_name, layout.get_layout_data_suffix(context))

    return placeholder_name


def get_provided_layouts():
    return get_provide_objects("xtheme_layout")
