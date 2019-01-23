# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.permissions import (
    AdminCustomModelPermissionDef, AdminDefaultModelPermissionDef
)
from shuup.admin.utils.urls import admin_url, derive_model_url, get_model_url
from shuup.admin.views.home import HelpBlockCategory, SimpleHelpBlock


class UserModule(AdminModule):
    name = _("Users")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:user.list")

    def get_urls(self):
        user_model = get_user_model()
        return [
            admin_url(
                r"^users/(?P<pk>\d+)/change-password/$",
                "shuup.admin.modules.users.views.UserChangePasswordView",
                name="user.change-password",
                permissions=[AdminCustomModelPermissionDef(user_model, "change_pwd", _("Can change passwords"))]
            ),
            admin_url(
                r"^users/(?P<pk>\d+)/reset-password/$",
                "shuup.admin.modules.users.views.UserResetPasswordView",
                name="user.reset-password",
                permissions=[AdminCustomModelPermissionDef(user_model, "reset_pwd", _("Can reset passwords"))]
            ),
            admin_url(
                r"^users/(?P<pk>\d+)/change-permissions/$",
                "shuup.admin.modules.users.views.UserChangePermissionsView",
                name="user.change-permissions",
                permissions=[
                    AdminCustomModelPermissionDef(user_model, "change_permissions", _("Can change permissions"))
                ]
            ),
            admin_url(
                r"^users/(?P<pk>\d+)/$",
                "shuup.admin.modules.users.views.UserDetailView",
                name="user.detail",
                permissions=[AdminDefaultModelPermissionDef(user_model, "view")]
            ),
            admin_url(
                r"^users/new/$",
                "shuup.admin.modules.users.views.UserDetailView",
                kwargs={"pk": None},
                name="user.new",
                permissions=[AdminDefaultModelPermissionDef(user_model, "add")]
            ),
            admin_url(
                r"^users/$",
                "shuup.admin.modules.users.views.UserListView",
                name="user.list",
                permissions=[AdminDefaultModelPermissionDef(user_model, "list")]
            ),
            admin_url(
                r"^users/(?P<pk>\d+)/login/$",
                "shuup.admin.modules.users.views.LoginAsUserView",
                name="user.login-as",
                permissions=[AdminCustomModelPermissionDef(user_model, "login_as", _("Can login as user"))]
            ),
            admin_url(
                r"^contacts/list-settings/",
                "shuup.admin.modules.settings.views.ListSettingsView",
                name="user.list_settings",
                permissions=[AdminDefaultModelPermissionDef(user_model, "list")]
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Users"),
                icon="fa fa-users",
                url="shuup_admin:user.list",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="permissions",
                ordering=1
            )
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            users = get_user_model().objects.filter(
                Q(username__icontains=query) |
                Q(email=query)
            )
            for i, user in enumerate(users[:10]):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(user),
                    url=get_model_url(user),
                    category=_("Contacts"),
                    relevance=relevance
                )

    def get_help_blocks(self, request, kind):
        yield SimpleHelpBlock(
            text=_("Add some users to help manage your shop"),
            actions=[{
                "text": _("New user"),
                "url": self.get_model_url(get_user_model(), "new")
            }],
            priority=3,
            category=HelpBlockCategory.CONTACTS,
            icon_url="shuup_admin/img/users.png",
            done=request.shop.staff_members.exclude(id=request.user.id).exists() if kind == "setup" else False,
            required=False
        )

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(get_user_model(), "shuup_admin:user", object, kind)
