# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.auth.models import Group as PermissionGroup
from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import Column, TextFilter
from shoop.admin.utils.views import PicotableListView


class PermissionGroupListView(PicotableListView):
    model = PermissionGroup
    columns = [
        Column(
            "name",
            _(u"Name"),
            sort_field="name",
            display="name",
            filter_config=TextFilter(
                filter_field="name",
                placeholder=_("Filter by name...")
            )
        ),
    ]

    def get_context_data(self, **kwargs):
        context = super(PermissionGroupListView, self).get_context_data(**kwargs)
        context["title"] = _("Permission Groups")
        return context
