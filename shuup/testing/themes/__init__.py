# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _

from shuup.xtheme import Theme


class ShuupTestingTheme(Theme):
    identifier = "shuup_testing"
    name = _("Shuup Testing Theme")
    author = "Shuup Team"
    template_dir = "shuup_testing"

    plugins = [__name__ + ".plugins.HighlightTestPlugin"]


class ShuupTestingThemeWithCustomBase(ShuupTestingTheme):
    identifier = "shuup_testing_with_custom_base_template"
    name = _("Shuup Testing Theme With Custom Base Template")
    default_template_dir = "default_templates"
