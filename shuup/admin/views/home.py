# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class HelpBlockCategory(Enum):
    PRODUCTS = 1
    ORDERS = 2
    CAMPAIGNS = 3
    CONTACTS = 4
    STOREFRONT = 5

    GENERAL = 200

    class Labels:
        PRODUCTS = _("Products")
        CONTACTS = _("Contacts")
        STOREFRONT = _("Storefront")
        CAMPAIGNS = _("Campaigns")
        ORDERS = _("Orders")
        GENERAL = _("General")


QUICKLINK_ORDER = [
    HelpBlockCategory.PRODUCTS,
    HelpBlockCategory.ORDERS,
    HelpBlockCategory.CAMPAIGNS,
    HelpBlockCategory.CONTACTS,
    HelpBlockCategory.STOREFRONT,
    HelpBlockCategory.GENERAL
]


class SimpleHelpBlock(object):
    def __init__(self, text, **kwargs):
        self.text = text
        self.description = kwargs.pop("description", "")
        self.actions = kwargs.pop("actions", [])
        self.icon_url = kwargs.pop("icon_url", None)
        self.priority = kwargs.pop("priority", 1)
        self.css_class = kwargs.pop("css_class", "")
        self.done = kwargs.pop("done", False)
        self.category = kwargs.pop("category", HelpBlockCategory.GENERAL)
