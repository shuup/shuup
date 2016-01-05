# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import Column, TextFilter
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Supplier


class SupplierListView(PicotableListView):
    model = Supplier
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
        Column("type", _(u"Type")),
        Column("module_identifier", _(u"Module"), display="get_module_display", sortable=True)
    ]

    def get_module_display(self, instance):
        return instance.module.name or _("No %s module") % self.model._meta.verbose_name
