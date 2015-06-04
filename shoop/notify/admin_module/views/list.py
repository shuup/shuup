# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from shoop.admin.toolbar import Toolbar, URLActionButton
from shoop.admin.utils.picotable import PicotableViewMixin, Column, TextFilter
from shoop.notify.admin_module.utils import get_name_map
from shoop.notify.models.script import Script


class ScriptListView(PicotableViewMixin, ListView):
    model = Script
    columns = [
        Column("name", _(u"Name"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("event_identifier", _(u"Event"), display="get_event_identifier_text"),
        Column("enabled", _(u"Enabled")),
    ]

    def get_object_url(self, instance):
        return reverse("shoop_admin:notify.script.edit", kwargs={"pk": instance.pk})

    def get_event_identifier_text(self, instance):
        if not hasattr(self, "_event_identifier_names"):
            self._event_identifier_names = dict(get_name_map("notify_event"))
        return self._event_identifier_names.get(instance.event_identifier, instance.event_identifier)

    def get_context_data(self, **kwargs):
        context = super(ScriptListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            URLActionButton(
                text="New Script", icon="fa fa-plus", extra_css_class="btn-success",
                url=reverse("shoop_admin:notify.script.new")
            )
        ])
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Event"), "text": item["event_identifier"]},
            {"title": _(u"Enabled"), "text": item["enabled"]}
        ]
