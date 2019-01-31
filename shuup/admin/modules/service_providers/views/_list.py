# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import ServiceProvider


class ServiceProviderListView(PicotableListView):
    model = ServiceProvider
    default_columns = [
        Column(
            "name", _("Name"), sort_field="base_translations__name",
            filter_config=TextFilter(
                filter_field="base_translations__name",
                placeholder=_("Filter by name..."))),
        Column("type", _(u"Type"), display="get_type_display", sortable=False),
    ]
    toolbar_buttons_provider_key = "service_provider_list_toolbar_provider"
    mass_actions_provider_key = "service_provider_mass_actions_provider"

    def get_type_display(self, instance):
        return instance._meta.verbose_name.capitalize()

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"text": self.get_type_display(instance)},
        ]
