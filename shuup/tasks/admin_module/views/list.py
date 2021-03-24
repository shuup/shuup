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
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import get_person_contact
from shuup.tasks.models import Task, TaskStatus, TaskType


class TaskListView(PicotableListView):
    model = Task
    default_columns = [
        Column(
            "name",
            _("Name"),
            sort_field="name",
            display="name",
            filter_config=TextFilter(filter_field="name", placeholder=_("Filter by name...")),
        ),
        Column(
            "creator",
            _("Creator"),
            display="get_creator_name_display",
            filter_config=TextFilter(filter_field="creator__name", placeholder=_("Filter by creator...")),
        ),
        Column("status", _("Status"), filter_config=ChoicesFilter(TaskStatus.choices), class_name="text-center"),
        Column("priority", _("Priority"), display="get_priority_display", class_name="text-center"),
        Column(
            "comments", _("Comments"), sort_field="comments", display="get_comments_count", class_name="text-center"
        ),
    ]
    toolbar_buttons_provider_key = "task_list_toolbar_provider"
    mass_actions_provider_key = "task_list_actions_provider"

    def get_comments_count(self, instance, **kwargs):
        return instance.comments.for_contact(get_person_contact(self.request.user)).count()

    def get_queryset(self):
        return Task.objects.for_shop(get_shop(self.request))

    def get_creator_name_display(self, instance, **kwargs):
        if not len(instance.creator.name):
            return "No name set (id: %d)" % instance.creator.id
        return instance.creator.name

    def get_priority_display(self, instance, **kwargs):
        return "%s" % instance.priority


class TaskTypeListView(PicotableListView):
    model = TaskType
    default_columns = [
        Column(
            "name",
            _("Name"),
            sort_field="name",
            display="name",
            filter_config=TextFilter(filter_field="translations__name", placeholder=_("Filter by name...")),
        )
    ]

    def get_queryset(self):
        return TaskType.objects.filter(shop=get_shop(self.request))
