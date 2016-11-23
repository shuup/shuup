# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme import Theme


class DefaultTheme(Theme):
    identifier = "shuup.themes.default_theme"
    name = _("Shuup Default Theme")
    author = _("Shuup Team")
    template_dir = "default_theme"

    def get_view(self, view_name):
        import shuup.front.themes.views as views
        return getattr(views, view_name, None)
