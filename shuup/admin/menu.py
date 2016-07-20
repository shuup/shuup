# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.datastructures import OrderedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions

ORDERS_MENU_CATEGORY = 1
PRODUCTS_MENU_CATEGORY = 2
CONTACTS_MENU_CATEGORY = 3
REPORTS_MENU_CATEGORY = 4
CAMPAIGNS_MENU_CATEGORY = 5
STOREFRONT_MENU_CATEGORY = 6
ADDONS_MENU_CATEGORY = 7
SETTINGS_MENU_CATEGORY = 8


MENU_CATEGORIES = [
    (ORDERS_MENU_CATEGORY, _("Orders"), "fa fa-inbox"),
    (PRODUCTS_MENU_CATEGORY, _("Products"), "fa fa-cube"),
    (CONTACTS_MENU_CATEGORY, _("Contacts"), "fa fa-users"),
    (REPORTS_MENU_CATEGORY, _("Reports"), "fa fa-bar-chart"),
    (CAMPAIGNS_MENU_CATEGORY, _("Campaigns"), "fa fa-bullhorn"),
    (STOREFRONT_MENU_CATEGORY, _("Storefront"), "fa fa-paint-brush"),
    (ADDONS_MENU_CATEGORY, _("Addons"), "fa fa-puzzle-piece"),
    (SETTINGS_MENU_CATEGORY, _("Settings"), "fa fa-tachometer")
]


class _MenuCategory(object):
    """
    Internal menu category object.
    """
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon
        self.entries = []

    def __iter__(self):
        return iter(sorted(self.entries, key=lambda e: e.ordering))


def get_menu_entry_categories(request):
    menu_categories = OrderedDict()
    menu_category_icons = {}
    for identifier, category_name, icon in MENU_CATEGORIES:
        menu_categories[identifier] = _MenuCategory(category_name, icon)
        menu_category_icons[identifier] = icon

    modules = list(get_modules())
    for module in modules:
        menu_category_icons.update(
            (force_text(key), force_text(value))
            for (key, value) in module.get_menu_category_icons().items()
            if key not in menu_category_icons
        )

    for module in modules:
        if get_missing_permissions(request.user, module.get_required_permissions()):
            continue
        for entry in (module.get_menu_entries(request=request) or ()):
            category_identifier = entry.category
            category = menu_categories.get(category_identifier) if category_identifier else None
            if not category:
                category_identifier = force_text(category_identifier or module.name)
                category = menu_categories.get(category_identifier)
                if not category:
                    menu_categories[category_identifier] = category = _MenuCategory(
                        name=category_identifier,
                        icon=menu_category_icons.get(category_identifier, "fa fa-circle")
                    )
            category.entries.append(entry)
    return [c for identifier, c in six.iteritems(menu_categories) if len(c.entries) > 0]
