# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import Toolbar
from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Supplier


class SupplierListView(PicotableListView):
    model = Supplier
    default_columns = [
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
    toolbar_buttons_provider_key = "supplier_list_toolbar_provider"
    mass_actions_provider_key = "supplier_list_mass_actions_provider"

    def get_queryset(self):
        return Supplier.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True)).not_deleted()

    def get_module_display(self, instance):
        return instance.module.name or _("No %s module") % self.model._meta.verbose_name

    def get_toolbar(self):
        if settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS:
            return super(SupplierListView, self).get_toolbar()
        else:
            return Toolbar.for_view(self)
