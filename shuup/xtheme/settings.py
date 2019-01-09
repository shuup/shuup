# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


#: Spec string for the Xtheme admin theme context
#:
#: You can use this to determine logic around which themes
#: are visible in your project admin. This function takes shop
#: `shuup.core.models.Shop` and should return `current_theme_classes`
#: and `current_theme` for context where `current_theme_classes`
#: is a list of `shuup.xtheme.models.ThemeSettings`.
SHUUP_XTHEME_ADMIN_THEME_CONTEXT = (
    "shuup.xtheme.admin_module.utils.get_theme_context")
