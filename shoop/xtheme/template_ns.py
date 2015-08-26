# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from jinja2.utils import contextfunction

from shoop.xtheme.editing import is_edit_mode
from shoop.xtheme.rendering import get_view_config


class XthemeNamespace(object):
    @contextfunction
    def get_view_name(self, context):
        return get_view_config(context).view_name

    @contextfunction
    def is_edit_mode(self, context):
        return is_edit_mode(context["request"])
