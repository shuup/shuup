# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.apps.provides import get_provide_objects
from shuup.xtheme.models import ThemeSettings


def get_theme_context(shop):
    themes = []
    active_theme = None

    # create one ThemeSettings for each theme if needed
    for theme in get_provide_objects("xtheme"):
        if not theme.identifier:
            continue

        theme_settings = ThemeSettings.objects.get_or_create(theme_identifier=theme.identifier, shop=shop)[0]
        themes.append(theme)

        if theme_settings.active:
            active_theme = theme

    return {
        "theme_classes": sorted(themes, key=lambda t: (t.name or t.identifier)),
        "current_theme": active_theme
    }
