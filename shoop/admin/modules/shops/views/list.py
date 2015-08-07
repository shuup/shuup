# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.picotable import Column, TextFilter, ChoicesFilter
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Shop, ShopStatus


class ShopListView(PicotableListView):
    model = Shop
    columns = [
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("domain", _(u"Domain")),
        Column("identifier", _(u"Identifier")),
        Column("status", _(u"Status"), filter_config=ChoicesFilter(choices=ShopStatus.choices)),
    ]
