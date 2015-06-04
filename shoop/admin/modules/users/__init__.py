# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.db.models import Q
from shoop.admin.base import AdminModule, MenuEntry, SearchResult
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.urls import admin_url, get_model_url, derive_model_url
import six


class UserModule(AdminModule):
    name = _("Users")
    category = _("Contacts")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:user.list")

    def get_urls(self):
        return [
            admin_url(
                "^users/(?P<pk>\d+)/change-password/$",
                "shoop.admin.modules.users.views.UserChangePasswordView",
                name="user.change-password"
            ),
            admin_url(
                "^users/(?P<pk>\d+)/reset-password/$",
                "shoop.admin.modules.users.views.UserResetPasswordView",
                name="user.reset-password"
            ),
            admin_url(
                "^users/(?P<pk>\d+)/change-permissions/$",
                "shoop.admin.modules.users.views.UserChangePermissionsView",
                name="user.change-permissions"
            ),
            admin_url(
                "^users/(?P<pk>\d+)/$",
                "shoop.admin.modules.users.views.UserDetailView",
                name="user.detail"
            ),
            admin_url(
                "^users/new/$",
                "shoop.admin.modules.users.views.UserDetailView",
                kwargs={"pk": None},
                name="user.new"
            ),
            admin_url(
                "^users/$",
                "shoop.admin.modules.users.views.UserListView",
                name="user.list"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.category: "fa fa-users"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Users"),
                icon="fa fa-users",
                url="shoop_admin:user.list",
                category=self.category
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
                    category=self.category,
                    relevance=relevance
                )

    def get_model_url(self, object, kind):
        return derive_model_url(get_user_model(), "shoop_admin:user", object, kind)
