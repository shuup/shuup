# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import admin_url, derive_model_url, get_model_url


class UserModule(AdminModule):
    name = _("Users")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:user.list")

    def get_urls(self):
        permissions = get_default_model_permissions(get_user_model())

        return [
            admin_url(
                "^users/(?P<pk>\d+)/change-password/$",
                "shuup.admin.modules.users.views.UserChangePasswordView",
                name="user.change-password",
                permissions=permissions
            ),
            admin_url(
                "^users/(?P<pk>\d+)/reset-password/$",
                "shuup.admin.modules.users.views.UserResetPasswordView",
                name="user.reset-password",
                permissions=permissions
            ),
            admin_url(
                "^users/(?P<pk>\d+)/change-permissions/$",
                "shuup.admin.modules.users.views.UserChangePermissionsView",
                name="user.change-permissions",
                permissions=permissions
            ),
            admin_url(
                "^users/(?P<pk>\d+)/$",
                "shuup.admin.modules.users.views.UserDetailView",
                name="user.detail",
                permissions=permissions
            ),
            admin_url(
                "^users/new/$",
                "shuup.admin.modules.users.views.UserDetailView",
                kwargs={"pk": None},
                name="user.new",
                permissions=permissions
            ),
            admin_url(
                "^users/$",
                "shuup.admin.modules.users.views.UserListView",
                name="user.list",
                permissions=permissions
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Users"),
                icon="fa fa-users",
                url="shuup_admin:user.list",
                category=SETTINGS_MENU_CATEGORY,
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

    def get_required_permissions(self):
        return get_default_model_permissions(get_user_model())

    def get_model_url(self, object, kind):
        return derive_model_url(get_user_model(), "shuup_admin:user", object, kind)
