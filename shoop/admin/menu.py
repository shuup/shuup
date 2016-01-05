# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text

from shoop.admin.module_registry import get_modules


class _MenuCategory(object):
    """
    Internal menu category object.
    """
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon
        self.entries = []

    def __iter__(self):
        return iter(sorted(self.entries, key=lambda e: e.text))


def get_menu_entry_categories(request):
    menu_categories = {}
    menu_category_icons = {}
    modules = list(get_modules())

    for module in modules:
        menu_category_icons.update(
            (force_text(key), force_text(value))
            for (key, value) in module.get_menu_category_icons().items()
        )

    for module in modules:
        for entry in (module.get_menu_entries(request=request) or ()):
            category_name = force_text(entry.category or module.name)
            category = menu_categories.get(category_name)
            if not category:
                menu_categories[category_name] = category = _MenuCategory(
                    name=category_name,
                    icon=menu_category_icons.get(category_name, "fa fa-circle")
                )
            category.entries.append(entry)

    return SortedDict(sorted((c.name, c) for c in sorted(menu_categories.values(), key=lambda c: c.name)))
