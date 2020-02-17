# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Attribute, AttributeType, AttributeVisibility


class AttributeListView(PicotableListView):
    model = Attribute
    default_columns = [
        Column("identifier", _("Identifier"), filter_config=TextFilter(
            filter_field="identifier",
            placeholder=_("Filter by identifier...")
        )),
        Column("name", _("Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("type", _("Type"), filter_config=ChoicesFilter(AttributeType.choices)),
        Column("visibility_mode", _("Visibility Mode"), filter_config=ChoicesFilter(AttributeVisibility.choices)),
        Column("searchable", _("Searchable")),
        Column("n_product_types", _("Used in # Product Types")),
    ]
    toolbar_buttons_provider_key = "attribute_list_toolbar_provider"
    mass_actions_provider_key = "attribute_list_mass_actions_provider"

    def get_queryset(self):
        return Attribute.objects.all().annotate(n_product_types=Count("product_types"))
