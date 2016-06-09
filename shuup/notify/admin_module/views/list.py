# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import Toolbar, URLActionButton
from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.notify.admin_module.utils import get_name_map
from shuup.notify.models.script import Script


class ScriptListView(PicotableListView):
    model = Script
    columns = [
        Column("name", _(u"Name"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("event_identifier", _(u"Event"), display="get_event_identifier_text"),
        Column("enabled", _(u"Enabled")),
    ]

    def get_object_url(self, instance):
        return reverse("shuup_admin:notify.script.edit", kwargs={"pk": instance.pk})

    def get_event_identifier_text(self, instance):
        if not hasattr(self, "_event_identifier_names"):
            self._event_identifier_names = dict(get_name_map("notify_event"))
        return self._event_identifier_names.get(instance.event_identifier, instance.event_identifier)

    def get_toolbar(self):
        return Toolbar([
            URLActionButton(
                text="New Script", icon="fa fa-plus", extra_css_class="btn-success",
                url=reverse("shuup_admin:notify.script.new")
            )
        ])

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Event"), "text": item["event_identifier"]},
            {"title": _(u"Enabled"), "text": item["enabled"]}
        ]
