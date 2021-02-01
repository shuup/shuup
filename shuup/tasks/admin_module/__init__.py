# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.dashboard import DashboardContentBlock
from shuup.admin.menu import CONTACTS_MENU_CATEGORY
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls, get_model_url
)
from shuup.core.models import get_person_contact
from shuup.tasks.models import Task, TaskStatus, TaskType
from shuup.utils.django_compat import force_text


class TaskAdminModule(AdminModule):
    name = _("Tasks")
    breadcrumbs_menu_entry = MenuEntry(name, "shuup_admin:task.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^tasks",
            view_template="shuup.tasks.admin_module.views.Task%sView",
            name_template="task.%s"
        ) + [
            admin_url(
                r"^tasks/(?P<pk>\d+)/delete/$",
                "shuup.tasks.admin_module.views.TaskDeleteView",
                name="task.delete"
            ),
            admin_url(
                r"^tasks/(?P<pk>\d+)/set_status/$",
                "shuup.tasks.admin_module.views.TaskSetStatusView",
                name="task.set_status"
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Tasks"),
                icon="fa fa-file-text",
                url="shuup_admin:task.list",
                category=CONTACTS_MENU_CATEGORY,
                ordering=4,
                aliases=[_("Show Tasks")]
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Task, "shuup_admin:task", object, kind)

    def get_dashboard_blocks(self, request):
        """ Return the latest 10 pending tasks """
        contact = get_person_contact(request.user)
        tasks = (
            Task.objects.for_shop(get_shop(request))
            .assigned_to(contact)
            .exclude(status__in=(TaskStatus.DELETED, TaskStatus.COMPLETED))
            .order_by("-priority")
        )[:10]

        if tasks.exists():
            tasks_block = DashboardContentBlock.by_rendering_template(
                "articles",
                request,
                "shuup/admin/tasks/tasks_dashboard_block.jinja",
                context=dict(tasks=tasks)
            )
            tasks_block.size = "medium"
            yield tasks_block

    def get_search_results(self, request, query):
        shop = get_shop(request)

        if len(query) >= 3:
            contact = get_person_contact(request.user)
            tasks = (
                Task.objects
                .for_shop(get_shop(request))
                .filter(name__icontains=query)
                .assigned_to(contact)
                .exclude(status__in=(TaskStatus.DELETED, TaskStatus.COMPLETED))
            )
            for task in tasks:
                yield SearchResult(
                    text=force_text("{task_name} [{task_status}]".format(**dict(
                        task_name=task.name,
                        task_status=task.status
                    ))),
                    url=get_model_url(task, shop=shop),
                    category=_("Tasks")
                )


class TaskTypeAdminModule(AdminModule):
    name = _("Task Types")
    breadcrumbs_menu_entry = MenuEntry(name, "shuup_admin:task_type.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^task_type",
            view_template="shuup.tasks.admin_module.views.TaskType%sView",
            name_template="task_type.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Task Types"),
                icon="fa fa-file-text",
                url="shuup_admin:task_type.list",
                category=CONTACTS_MENU_CATEGORY,
                ordering=5,
                aliases=[_("Show Task Types")]
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(TaskType, "shuup_admin:task_type", object, kind)
