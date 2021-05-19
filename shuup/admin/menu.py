# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.datastructures import OrderedDict
from django.utils.translation import get_language, ugettext_lazy as _

from shuup import configuration
from shuup.admin.base import BaseMenuEntry
from shuup.admin.module_registry import get_modules
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.views.home import QUICKLINK_ORDER
from shuup.apps.provides import get_provide_objects
from shuup.utils.django_compat import force_text

ORDERS_MENU_CATEGORY = 1
PRODUCTS_MENU_CATEGORY = 2
CONTACTS_MENU_CATEGORY = 3
REPORTS_MENU_CATEGORY = 4
CAMPAIGNS_MENU_CATEGORY = 5
STOREFRONT_MENU_CATEGORY = 6
ADDONS_MENU_CATEGORY = 7
SETTINGS_MENU_CATEGORY = 8
CONTENT_MENU_CATEGORY = 9
LOG_MENU_CATEGORY = 10
MESSAGES_MENU_CATEGORY = 11

MAIN_MENU = [
    {
        "identifier": ORDERS_MENU_CATEGORY,
        "title": _("Orders"),
        "icon": "fa fa-inbox",
    },
    {
        "identifier": PRODUCTS_MENU_CATEGORY,
        "title": _("Products"),
        "icon": "fa fa-cube",
    },
    {
        "identifier": CONTACTS_MENU_CATEGORY,
        "title": _("Contacts"),
        "icon": "fa fa-users",
    },
    {
        "identifier": CAMPAIGNS_MENU_CATEGORY,
        "title": _("Campaigns"),
        "icon": "fa fa-bullhorn",
    },
    {
        "identifier": CONTENT_MENU_CATEGORY,
        "title": _("Content"),
        "icon": "fa fa-columns",
    },
    {
        "identifier": REPORTS_MENU_CATEGORY,
        "title": _("Reports"),
        "icon": "fa fa-bar-chart",
    },
    {
        "identifier": STOREFRONT_MENU_CATEGORY,
        "title": _("Shops"),
        "icon": "fa fa-shopping-basket",
    },
    {
        "identifier": ADDONS_MENU_CATEGORY,
        "title": _("Addons"),
        "icon": "fa fa-puzzle-piece",
    },
    {
        "identifier": SETTINGS_MENU_CATEGORY,
        "title": _("Settings"),
        "icon": "fa fa-tachometer",
    },
    {
        "identifier": LOG_MENU_CATEGORY,
        "title": _("Logs"),
        "icon": "fa fa-archive",
    },
    {
        "identifier": MESSAGES_MENU_CATEGORY,
        "title": _("Messages"),
        "icon": "fa fa-envelope",
    },
]

CUSTOM_ADMIN_MENU_USER_PREFIX = "admin_menu_user_{}"
CUSTOM_ADMIN_MENU_SUPPLIER_KEY = "admin_menu_supplier"
CUSTOM_ADMIN_MENU_STAFF_KEY = "admin_menu_staff"
CUSTOM_ADMIN_MENU_SUPERUSER_KEY = "admin_menu_superuser"


class _MenuCategory(BaseMenuEntry):
    """
    Internal menu category object.
    """

    def __init__(self, identifier, name, icon):
        self.identifier = identifier
        self.name = name
        self.icon = icon
        self.children = []
        self.entries = []

    def contains_badges(self, request):
        return any(bool(entry.get_badge(request)) for entry in self.entries)


def extend_main_menu(menu):
    for menu_updater in get_provide_objects("admin_main_menu_updater"):
        menu = menu_updater(menu).update()
    return menu


def customize_menu(entries, request):  # noqa (C901)
    """
    Merge system menu with customized admin menu
    """
    customized_admin_menu = configuration.get(None, CUSTOM_ADMIN_MENU_USER_PREFIX.format(request.user.pk))
    if not customized_admin_menu:
        supplier = get_supplier(request)
        if supplier:
            customized_admin_menu = configuration.get(None, CUSTOM_ADMIN_MENU_SUPPLIER_KEY)
        elif getattr(request.user, "is_superuser", False):
            customized_admin_menu = configuration.get(None, CUSTOM_ADMIN_MENU_SUPERUSER_KEY)
        else:
            customized_admin_menu = configuration.get(None, CUSTOM_ADMIN_MENU_STAFF_KEY)

    if customized_admin_menu and isinstance(customized_admin_menu, dict):
        """
        If menu configuration is stored to dict try to find right configuration with current language
        """
        customized_admin_menu = customized_admin_menu.get(get_language())

    if customized_admin_menu:

        def unset_mismatched(menu):
            """
            find and remove unmatched entries from customized menu tree
            it can be when menu entry was removed from system
            """
            indexes = []
            for index, entry in enumerate(menu.get("entries", [])):
                unset_mismatched(entry)
                if isinstance(entry, dict):
                    indexes.append(index)
            for index in indexes[::-1]:
                del menu["entries"][index]

        def find_entry(menu, entry):
            """
            find recursively entry in menu
            """
            if menu["id"] == entry.id:
                return menu
            for node in menu.get("entries", []):
                n = find_entry(node, entry)
                if n:
                    return n

        def assign_entry(customized_menu, entry):
            """
            Find and replace customized entry with system menu entry
            set entry name, hidden flag from customized menu entry
            """
            custom_entries = customized_menu.get("entries", [])
            for index, node in enumerate(custom_entries):
                if node["id"] == entry.id:
                    custom_entry = custom_entries[index]
                    entry.name = custom_entry["name"]
                    entry.is_hidden = custom_entry["is_hidden"]
                    entry.entries = custom_entry.get("entries", [])
                    entry.ordering = index
                    custom_entries[index] = entry
                    return custom_entries[index]
                else:
                    return_entry = assign_entry(custom_entries[index], entry)
                    if return_entry:
                        return return_entry

        def transform_menu(customized_menu, menu):
            """
            Recursively sort system menu entries and assign it to the customized menu
            """
            indexes = []
            for index, entry in enumerate(menu.entries):
                transform_menu(customized_menu, entry)
                custom_entry = assign_entry(customized_menu, entry)
                if not custom_entry:
                    parent_menu = find_entry(customized_menu, menu)
                    if parent_menu:
                        parent_menu.get("entries", []).append(entry)
                        indexes.append(index)
                else:
                    indexes.append(index)
            # remove assigned entries from system menu
            for index in indexes[::-1]:
                del menu.entries[index]
            return menu

        customized_menu = {
            "id": "root",
            "name": "root",
            "entries": customized_admin_menu,
        }
        system_menu = BaseMenuEntry()
        system_menu.identifier = "root"
        system_menu.entries = entries
        transform_menu(customized_menu, system_menu)
        unset_mismatched(customized_menu)

        return customized_menu["entries"] + system_menu["entries"]
    else:
        return entries


def get_menu_entry_categories(request):  # noqa (C901)
    menu_categories = OrderedDict()

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

        for entry in module.get_menu_entries(request=request) or ():
            category = menu_categories.get(entry.category)
            if not category:
                category_identifier = force_text(entry.category or module.name)
                category = menu_categories.get(category_identifier)
                if not category:
                    menu_categories[category_identifier] = category = _MenuCategory(
                        identifier=category_identifier,
                        name=category_identifier,
                        icon=menu_category_icons.get(category_identifier, "fa fa-circle"),
                    )
            category.entries.append(entry)
            all_categories.add(category)

    # clean categories that eventually have no children or entries
    categories = []
    for cat in all_categories:
        if not cat.entries:
            continue
        categories.append(cat)
    clean_categories = [c for menu_identifier, c in six.iteritems(menu_categories) if c in categories]

    return customize_menu(clean_categories, request)


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
