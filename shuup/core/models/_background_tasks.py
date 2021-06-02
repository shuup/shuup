# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField


class BackgroundTask(models.Model):
    queue = models.CharField(max_length=128, verbose_name=_("queue name"), db_index=True)
    identifier = models.CharField(max_length=128, verbose_name=_("task identifier"), unique=True)
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))
    function = models.TextField(verbose_name=_("task function"))
    arguments = JSONField(blank=True, null=True, verbose_name=_("task arguments"))
    shop = models.ForeignKey(
        on_delete=models.SET_NULL, to="shuup.Shop", verbose_name=_("shop"), related_name="background_tasks", null=True
    )
    supplier = models.ForeignKey(
        on_delete=models.SET_NULL,
        to="shuup.Supplier",
        verbose_name=_("supplier"),
        related_name="background_tasks",
        null=True,
    )
    user = models.ForeignKey(
        on_delete=models.SET_NULL,
        to=get_user_model(),
        verbose_name=_("user"),
        related_name="background_tasks",
        null=True,
    )

    class Meta:
        verbose_name = _("background task")
        verbose_name_plural = _("background tasks")


class BackgroundTaskExecutionStatus(Enum):
    RUNNING = 0
    SUCCESS = 1
    ERROR = 2

    class Label:
        RUNNING = _("running")
        SUCCESS = _("success")
        ERROR = _("error")


class BackgroundTaskExecution(models.Model):
    task = models.ForeignKey(
        on_delete=models.CASCADE,
        to=BackgroundTask,
        verbose_name=_("background task"),
        related_name="executions",
    )
    started_on = models.DateTimeField(verbose_name=_("started on"), auto_now_add=True)
    finished_on = models.DateTimeField(verbose_name=_("finished on"), null=True)
    status = EnumIntegerField(
        BackgroundTaskExecutionStatus, default=BackgroundTaskExecutionStatus.RUNNING, verbose_name=_("status")
    )
    result = JSONField(blank=True, null=True, verbose_name=_("results"))
    error_log = models.TextField(verbose_name=_("error log"), blank=True, null=True)

    class Meta:
        verbose_name = _("background task execution")
        verbose_name_plural = _("background task executions")
