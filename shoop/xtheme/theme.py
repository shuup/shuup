# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps.provides import get_provide_objects


class Theme(object):
    # The identifier for this theme. Used for theme selection.
    identifier = None

    # Directory prefix for this theme's template files.
    # If `None`, the `identifier` is used instead
    template_dir = None

    # List of global placeholder names.
    # TODO: (These could be ignored in per-view editing, or something?)
    global_placeholders = []

    global_variables = []


def get_current_theme():
    # TODO: Don't just use the first theme, silly
    for theme_cls in get_provide_objects("xtheme"):
        if theme_cls.identifier:
            return theme_cls
    return Theme  # Ah well!
