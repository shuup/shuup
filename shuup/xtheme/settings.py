# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


#: Spec string for the Xtheme admin theme context.
#:
#: You can use this to determine logic around which themes
#: are visible in your project Admin Panel. This function takes shop
#: `shuup.core.models.Shop` and should return `current_theme_classes`
#: and `current_theme` for context, where `current_theme_classes`
#: is a list of `shuup.xtheme.models.ThemeSettings`.
SHUUP_XTHEME_ADMIN_THEME_CONTEXT = "shuup.xtheme.admin_module.utils.get_theme_context"

#: Spec to control Xtheme resource injections.
#:
#: Include your template names here to prevent xtheme
#: injecting resources. This does not expect the template
#: to exist.
#:
#: Can be useful in situations, where you have `html` and `body`
#: HTML tags inside the actual template structure.
SHUUP_XTHEME_EXCLUDE_TEMPLATES_FROM_RESOUCE_INJECTION = [
    "notify/admin/script_item_editor.jinja",
]

#: Cache placeholders
#:
#: This useful when you have plugins does no depend on
#: context which they should not.
#:
#: By default do not create plugins which are depended
#: on context. Instead try to make those asynchronous
#: so those are not rendered server side during initial
#: page load.
SHUUP_XTHEME_USE_PLACEHOLDER_CACHE = False
