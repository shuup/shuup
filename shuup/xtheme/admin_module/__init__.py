# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.template import engines
from django.utils.translation import ugettext_lazy as _
from django_jinja.backend import Jinja2
from typing import Iterable

from shuup.admin.base import AdminModule, MenuEntry, Notification
from shuup.admin.menu import CONTENT_MENU_CATEGORY
from shuup.admin.utils.object_selector import get_object_selector_permission_name
from shuup.admin.utils.urls import admin_url, derive_model_url, get_edit_and_list_urls
from shuup.admin.views.home import HelpBlockCategory, SimpleHelpBlock
from shuup.utils.django_compat import reverse
from shuup.xtheme._theme import get_current_theme
from shuup.xtheme.engine import XthemeEnvironment
from shuup.xtheme.models import Font, Snippet


class XthemeAdminModule(AdminModule):
    """
    Admin module for Xtheme.

    Allows theme activation/deactivation and further configuration.
    """

    name = _("Shuup Extensible Theme Engine")
    breadcrumbs_menu_entry = MenuEntry(_("Themes"), "shuup_admin:xtheme.config", category=CONTENT_MENU_CATEGORY)

    def get_urls(self):  # doccov: ignore
        return [
            admin_url(
                r"^xtheme/guide/(?P<theme_identifier>.+?)/",
                "shuup.xtheme.admin_module.views.ThemeGuideTemplateView",
                name="xtheme.guide",
            ),
            admin_url(
                r"^xtheme/configure/(?P<theme_identifier>.+?)/",
                "shuup.xtheme.admin_module.views.ThemeConfigDetailView",
                name="xtheme.config_detail",
            ),
            admin_url(
                r"^xtheme/admin-configure/",
                "shuup.xtheme.admin_module.views.AdminThemeConfigDetailView",
                name="xtheme.admin_config_detail",
            ),
            admin_url(r"^xtheme/theme", "shuup.xtheme.admin_module.views.ThemeConfigView", name="xtheme.config"),
        ]

    def get_menu_entries(self, request):  # doccov: ignore
        return [
            MenuEntry(
                text=_("Themes"),
                icon="fa fa-paint-brush",
                url="shuup_admin:xtheme.config",
                category=CONTENT_MENU_CATEGORY,
                ordering=1,
            ),
        ]

    def get_help_blocks(self, request, kind):
        theme = getattr(request, "theme", None) or get_current_theme(request.shop)
        if kind == "quicklink" and theme:
            yield SimpleHelpBlock(
                text=_("Customize the look and feel of your shop"),
                actions=[
                    {
                        "text": _("Customize theme"),
                        "url": reverse(
                            "shuup_admin:xtheme.config_detail", kwargs={"theme_identifier": theme.identifier}
                        ),
                    }
                ],
                priority=200,
                category=HelpBlockCategory.STOREFRONT,
                icon_url="xtheme/theme.png",
            )

    def get_notifications(self, request):
        try:
            engine = engines["jinja2"]
        except KeyError:
            engine = None

        if engine and isinstance(engine, Jinja2):  # The engine is what we expect...
            if isinstance(engine.env, XthemeEnvironment):  # ... and it's capable of loading themes...
                if not (getattr(request, "theme", None) or get_current_theme(request.shop)):
                    # ... but there's no theme active?!
                    # Panic!
                    yield Notification(
                        text=_("No theme is active. Click here to activate one."),
                        title=_("Theming"),
                        url="shuup_admin:xtheme.config",
                    )


class XthemeFontsAdminModule(AdminModule):
    name = _("Shuup Extensible Theme Engine Fonts")
    breadcrumbs_menu_entry = MenuEntry(_("Fonts"), "shuup_admin:xtheme.font.list", category=CONTENT_MENU_CATEGORY)

    def get_urls(self):  # doccov: ignore
        return [
            admin_url(
                r"^xtheme/font/$",
                "shuup.xtheme.admin_module.views.FontListView",
                name="xtheme.font.list",
            ),
            admin_url(
                r"^xtheme/font/new/$",
                "shuup.xtheme.admin_module.views.FontEditView",
                name="xtheme.font.new",
                kwargs={"pk": None},
            ),
            admin_url(
                r"^xtheme/font/(?P<pk>\d+)/$",
                "shuup.xtheme.admin_module.views.FontEditView",
                name="xtheme.font.edit",
            ),
        ]

    def get_menu_entries(self, request):  # doccov: ignore
        return [
            MenuEntry(
                text=_("Fonts"),
                icon="fa fa-font",
                url="shuup_admin:xtheme.font.list",
                category=CONTENT_MENU_CATEGORY,
                ordering=10,
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Font, "shuup_admin:xtheme.font", object, kind)

    def get_extra_permissions(self) -> Iterable[str]:
        return [get_object_selector_permission_name(Font)]

    def get_permissions_help_texts(self) -> Iterable[str]:
        return {get_object_selector_permission_name(Font): _("Allow the user to select fonts in admin.")}


class XthemeSnippetsAdminModule(AdminModule):
    name = _("Shuup Extensible Theme Engine Snippets")
    breadcrumbs_menu_entry = MenuEntry(_("Snippets"), "shuup_admin:xtheme_snippet.list", category=CONTENT_MENU_CATEGORY)

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix=r"^xtheme/snippet",
            view_template="shuup.xtheme.admin_module.views.Snippet%sView",
            name_template="xtheme_snippet.%s",
        ) + [
            admin_url(
                r"^xtheme/snippet/(?P<pk>\d+)/delete/$",
                "shuup.xtheme.admin_module.views.SnippetDeleteView",
                name="xtheme_snippet.delete",
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Theme Custom CSS/JS"),
                icon="fa fa-magic",
                url="shuup_admin:xtheme_snippet.list",
                category=CONTENT_MENU_CATEGORY,
                ordering=2,
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Snippet, "shuup_admin:xtheme_snippet", object, kind)
