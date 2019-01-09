# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.datastructures import OrderedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.views.home import QUICKLINK_ORDER
from shuup.apps.provides import get_provide_objects

ORDERS_MENU_CATEGORY = 1
PRODUCTS_MENU_CATEGORY = 2
CONTACTS_MENU_CATEGORY = 3
REPORTS_MENU_CATEGORY = 4
CAMPAIGNS_MENU_CATEGORY = 5
STOREFRONT_MENU_CATEGORY = 6
ADDONS_MENU_CATEGORY = 7
SETTINGS_MENU_CATEGORY = 8
CONTENT_MENU_CATEGORY = 9

MAIN_MENU = [
    {
        "identifier": ORDERS_MENU_CATEGORY,
        "title": _("Orders"),
        "icon": "fa fa-inbox",
        "children": [
            {
                "identifier": "orders",
                "title": _("Orders")
            },
        ]
    },
    {
        "identifier": PRODUCTS_MENU_CATEGORY,
        "title": _("Products"),
        "icon": "fa fa-cube",
        "children": [
            {
                "identifier": "products",
                "title": _("Products")
            },
        ]
    },
    {
        "identifier": CONTACTS_MENU_CATEGORY,
        "title": _("Contacts"),
        "icon": "fa fa-users",
        "children": []
    },
    {
        "identifier": CAMPAIGNS_MENU_CATEGORY,
        "title": _("Campaigns"),
        "icon": "fa fa-bullhorn",
        "children": []
    },
    {
        "identifier": CONTENT_MENU_CATEGORY,
        "title": _("Content"),
        "icon": "fa fa-columns",
        "children": [
            {
                "identifier": "elements",
                "title": _("Elements")
            },
            {
                "identifier": "design",
                "title": _("Design")
            },
            {
                "identifier": "other",
                "title": _("Other"),
            }
        ]
    },
    {
        "identifier": REPORTS_MENU_CATEGORY,
        "title": _("Reports"),
        "icon": "fa fa-bar-chart",
        "children": []
    },
    {
        "identifier": STOREFRONT_MENU_CATEGORY,
        "title": _("Shops"),
        "icon": "fa fa-shopping-basket",
        "children": [
            {
                "identifier": "settings",
                "title": _("Settings")
            },
            {
                "identifier": "payment_shipping",
                "title": _("Payment & Shipping")
            },
            {
                "identifier": "currency",
                "title": _("Currency")
            },
            {
                "identifier": "attributes",
                "title": _("Attributes")
            },
            {
                "identifier": "other_settings",
                "title": _("Other settings")
            },
        ]
    },
    {
        "identifier": ADDONS_MENU_CATEGORY,
        "title": _("Addons"),
        "icon": "fa fa-puzzle-piece",
        "children": []
    },
    {
        "identifier": SETTINGS_MENU_CATEGORY,
        "title": _("Settings"),
        "icon": "fa fa-tachometer",
        "children": [
            {
                "identifier": "data_transfer",
                "title": _("Data Transfer")
            },
            {
                "identifier": "taxes",
                "title": _("Taxes")
            },
            {
                "identifier": "permissions",
                "title": _("Permissions")
            },
            {
                "identifier": "other_settings",
                "title": _("Other Settings")
            },
        ]
    }
]


class _MenuCategory(object):
    """
    Internal menu category object.
    """
    def __init__(self, identifier, name, icon):
        self.identifier = identifier
        self.name = name
        self.icon = icon
        self.children = []
        self.entries = []

    def __iter__(self):
        return iter(sorted(self.entries, key=lambda e: e.ordering))


def extend_main_menu(menu):
    for menu_updater in get_provide_objects("admin_main_menu_updater"):
        menu = menu_updater(menu).update()
    return menu


def get_menu_entry_categories(request): # noqa (C901)
    menu_categories = OrderedDict()
    menu_children = OrderedDict()

    # Update main menu from provides
    main_menu = extend_main_menu(MAIN_MENU)

    menu_category_icons = {}
    for menu_item in main_menu:
        identifier = menu_item["identifier"]
        icon = menu_item["icon"]
        menu_categories[identifier] = _MenuCategory(
            identifier=identifier,
            name=menu_item["title"],
            icon=icon,
        )
        for child in menu_item["children"]:
            child_identifier = "%s:%s" % (identifier, child["identifier"])
            child_category = _MenuCategory(child["identifier"], child["title"], None)
            menu_children[child_identifier] = child_category
            menu_categories[identifier].children.append(child_category)

        menu_category_icons[identifier] = icon

    modules = list(get_modules())
    for module in modules:
        menu_category_icons.update(
            (force_text(key), force_text(value))
            for (key, value) in module.get_menu_category_icons().items()
            if key not in menu_category_icons
        )

    all_categories = set()
    for module in modules:
        if get_missing_permissions(request.user, module.get_required_permissions()):
            continue

        for entry in (module.get_menu_entries(request=request) or ()):
            category_identifier = entry.category
            subcategory = entry.subcategory

            entry_identifier = "%s:%s" % (category_identifier, subcategory) if subcategory else category_identifier
            menu_items = menu_children if subcategory else menu_categories

            category = menu_items.get(entry_identifier)
            if not category:
                category_identifier = force_text(category_identifier or module.name)
                category = menu_items.get(category_identifier)
                if not category:
                    menu_items[category_identifier] = category = _MenuCategory(
                        identifier=category_identifier,
                        name=category_identifier,
                        icon=menu_category_icons.get(category_identifier, "fa fa-circle")
                    )
            category.entries.append(entry)
            if subcategory:
                parent = menu_categories.get(category_identifier)
                all_categories.add(parent)
            else:
                all_categories.add(category)

    # clean categories that eventually have no children or entries
    categories = []
    for cat in all_categories:
        cat.children = [c for c in cat.children if c.entries or c.children]
        if not cat.entries and not cat.children:
            continue
        categories.append(cat)
    return [c for menu_identifier, c in six.iteritems(menu_categories) if c in categories]


def get_quicklinks(request):
    quicklinks = OrderedDict()
    for block in QUICKLINK_ORDER:
        quicklinks[block] = []

    for module in get_modules():
        if get_missing_permissions(request.user, module.get_required_permissions()):
            continue
        for help_block in module.get_help_blocks(request, kind="quicklink"):
            quicklinks[help_block.category].append(help_block)

    links = quicklinks.copy()
    for block, data in six.iteritems(links):
        if not quicklinks[block]:
            quicklinks.pop(block)
    return quicklinks
