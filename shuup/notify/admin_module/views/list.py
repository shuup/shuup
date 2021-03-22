# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import JavaScriptActionButton, Toolbar, URLActionButton
from shuup.admin.utils.picotable import Column, TextFilter, true_or_false_filter
from shuup.admin.utils.views import PicotableListView
from shuup.notify.admin_module.utils import get_name_map
from shuup.notify.models.script import Script
from shuup.utils.django_compat import reverse


class ScriptListView(PicotableListView):
    template_name = "notify/admin/list_script.jinja"

    model = Script
    default_columns = [
        Column("name", _("Name"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("event_identifier", _("Event"), display="get_event_identifier_text"),
        Column("enabled", _("Enabled"), filter_config=true_or_false_filter),
    ]
    toolbar_buttons_provider_key = "notify_list_toolbar_provider"
    mass_actions_provider_key = "notify_list_actions_provider"

    def get_object_url(self, instance):
        return reverse("shuup_admin:notify.script.edit", kwargs={"pk": instance.pk})

    def get_event_identifier_text(self, instance):
        if not hasattr(self, "_event_identifier_names"):
            self._event_identifier_names = dict(get_name_map("notify_event"))
        return self._event_identifier_names.get(instance.event_identifier, instance.event_identifier)

    def get_toolbar(self):
        return Toolbar(
            [
                URLActionButton(
                    text=_("New Script"),
                    icon="fa fa-plus",
                    extra_css_class="btn-success",
                    url=reverse("shuup_admin:notify.script.new"),
                ),
                JavaScriptActionButton(text=_("New From Template"), icon="fa fa-book", onclick="showScriptTemplates()"),
            ],
            view=self,
        )

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _("Event"), "text": item.get("event_identifier")},
            {"title": _("Enabled"), "text": item.get("enabled")},
        ]

    def get_queryset(self):
        return super(ScriptListView, self).get_queryset().filter(shop=get_shop(self.request))
