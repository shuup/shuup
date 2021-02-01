# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.admin.menu import PRODUCTS_MENU_CATEGORY
from shuup.core.utils.menu import MainMenuUpdater


class TestAdminMainMenuUpdater(MainMenuUpdater):
    updates = {
        PRODUCTS_MENU_CATEGORY: [
            {"identifier": "test_0", "title": "Test 0"},
            {"identifier": "test_1", "title": "Test 1"},
        ],
    }
