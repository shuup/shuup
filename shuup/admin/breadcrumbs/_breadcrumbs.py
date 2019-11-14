# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import MenuEntry
from shuup.admin.module_registry import get_modules
from shuup.utils.django_compat import force_text


def _get_admin_module_for_url(url_names):
    for module in get_modules():
        for url in module.get_urls():
            if url.name in url_names:
                return module


class Breadcrumbs(object):
    @classmethod
    def infer(cls, context):
        """
        Infer breadcrumbs from the rendering context.

        :param context: Jinja Context
        :type context: jinja2.runtime.Context
        :return: Breadcrumbs object or None if things fail
        :rtype: Breadcrumbs|None
        """
        request = context["request"]
        if not getattr(request, "resolver_match", None):
            # If we don't have a resolver match, we can't infer anything.
            return None

        url_names = (
            request.resolver_match.url_name,
            "%s:%s" % (request.resolver_match.app_name, request.resolver_match.url_name)
        )
        url_admin_module = _get_admin_module_for_url(url_names)

        # Synthesize a menu entry for the current view.
        current_view_entry = MenuEntry(url=request.path, text="")

        if url_admin_module:
            # See if we have an idea for the title of this view from the menu entries
            for entry in url_admin_module.get_menu_entries(request):
                if entry.original_url in url_names:
                    current_view_entry.text = entry.text
                    break

        # See if we have a title for the synthesized entry in the context.
        view = context.get("view")  # This should be the CBV view object.
        title = (
            context.get("title") or
            context.get("breadcrumb_title") or
            (view and getattr(view, "title", None))
        )

        if title:
            current_view_entry.text = force_text(title)

        # Begin building the entries...

        entries = []

        # See if we have the top level menu entry ("Contacts" for example).
        if url_admin_module and url_admin_module.breadcrumbs_menu_entry:
            # (But don't duplicate steps)
            if url_admin_module.breadcrumbs_menu_entry.url != request.path or not current_view_entry.text:
                entries.append(url_admin_module.breadcrumbs_menu_entry)

        # See if the view declares parents...
        parent_getter = getattr(view, "get_breadcrumb_parents", None)
        if parent_getter:
            entries.extend(parent_getter() or ())

        # If the current entry seems valid (would be visible), then go for it!
        if current_view_entry.text:
            entries.append(current_view_entry)

        return cls(entries)

    def __init__(self, entries):
        self.entries = list(entries)

    def get_entries(self, request):
        if not len(self.entries):
            return

        entries = ([
            MenuEntry(_("Home"), url="shuup_admin:dashboard")
        ] + self.entries)
        return entries
