# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class MainMenuUpdater(object):

    """
    To update items add for example
    updates = {
        PRODUCTS_MENU_CATEGORY: [{"identifier": "subscriptions", "title": _("Subscriptions")}],
        ORDERS_MENU_CATEGORY: [{"identifier": "subscriptions", "title": _("Subscriptions")}]
    }
    """
    updates = {}

    def __init__(self, menu):
        self.menu = menu

    def update(self):
        """
        Update the `shuup.admin.menu.MAIN_MENU`
        :return:
        """
        for item in self.menu:
            for child in self.updates.get(item["identifier"], []):
                if child not in item["children"]:
                    item["children"].append(child)
        return self.menu
