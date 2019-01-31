# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import Toolbar
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Shop, ShopStatus
from shuup.core.settings_provider import ShuupSettings


class ShopListView(PicotableListView):
    model = Shop
    default_columns = [
        Column("logo",
               _(u"Logo"),
               display="logo",
               class_name="text-center",
               raw=True,
               ordering=1,
               sortable=False),
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("domain", _(u"Domain")),
        Column("identifier", _(u"Identifier")),
        Column("status", _(u"Status"), filter_config=ChoicesFilter(choices=ShopStatus.choices)),
    ]
    toolbar_buttons_provider_key = "shop_list_toolbar_provider"
    mass_actions_provider_key = "shop_list_mass_actions_provider"

    def get_queryset(self):
        return Shop.objects.get_for_user(self.request.user)

    def get_toolbar(self):
        if ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            return super(ShopListView, self).get_toolbar()
        else:
            return Toolbar.for_view(self)
