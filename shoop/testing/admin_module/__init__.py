# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import admin_url
from django.utils.translation import ugettext_lazy as _


class TestingAdminModule(AdminModule):
    def get_urls(self):
        return [
            admin_url("^mocker/$", "shoop.testing.admin_module.mocker_view.MockerView", name="mocker")
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text="Create Mock Objects",
                category=_("System"),
                url="shoop_admin:mocker",
                icon="fa fa-star"
            )
        ]
