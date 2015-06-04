# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shoop.admin.base import AdminModule, Notification, MenuEntry
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.urls import admin_url, derive_model_url
from shoop.notify.enums import Priority
from shoop.notify.models import Notification as NotificationModel, Script


class NotifyAdminModule(AdminModule):
    name = _(u"Notifications")
    breadcrumbs_menu_entry = MenuEntry(name, "shoop_admin:notify.script.list")

    def get_urls(self):
        return [
            admin_url(
                "notify/script-item-editor/",
                "shoop.notify.admin_module.views.script_item_editor",
                name="notify.script-item-editor"
            ),
            admin_url(
                "notify/script/content/(?P<pk>\d+)/",
                "shoop.notify.admin_module.views.EditScriptContentView",
                name="notify.script.edit-content"
            ),
            admin_url(
                "notify/script/(?P<pk>\d+)/",
                "shoop.notify.admin_module.views.EditScriptView",
                name="notify.script.edit"
            ),
            admin_url(
                "notify/script/new/",
                "shoop.notify.admin_module.views.EditScriptView",
                kwargs={"pk": None},
                name="notify.script.new"
            ),
            admin_url(
                "notify/script/",
                "shoop.notify.admin_module.views.ScriptListView",
                name="notify.script.list"
            ),
            admin_url(
                "notify/mark-read/(?P<pk>\d+)/$",
                self.mark_notification_read_view,
                name="notify.mark-read"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-envelope-o"}

    def get_menu_entries(self, request):
        category = _("Notifications")
        return [
            MenuEntry(
                text=_("Notification scripts"), icon="fa fa-code",
                url="shoop_admin:notify.script.list",
                category=category, aliases=[_("Show notification scripts")]
            )
        ]

    @csrf_exempt
    def mark_notification_read_view(self, request, pk):
        if request.method == "POST":
            try:
                notif = NotificationModel.objects.for_user(request.user).get(pk=pk)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "no such notification"})
            notif.mark_read(request.user)
            return JsonResponse({"ok": True})
        return JsonResponse({"error": "POST only"})

    def get_notifications(self, request):
        notif_qs = NotificationModel.objects.unread_for_user(request.user).order_by("-id")[:15]

        for notif in notif_qs:
            if notif.priority == Priority.HIGH:
                kind = "warning"
            elif notif.priority == Priority.CRITICAL:
                kind = "danger"
            else:
                kind = "info"

            yield Notification(
                text=notif.message,
                url=notif.url,
                kind=kind,
                dismissal_url=reverse("shoop_admin:notify.mark-read", kwargs={"pk": notif.pk}),
                datetime=notif.created_on
            )

    def get_model_url(self, object, kind):
        return derive_model_url(Script, "shoop_admin:notify.script", object, kind)
