# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import six

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField


@python_2_unicode_compatible
class BackgroundTask(models.Model):
    queue = models.CharField(
        max_length=255,
        verbose_name=_("queue name"),
        db_index=True
    )
    identifier = models.CharField(
        max_length=255,
        verbose_name=_("queue identifier"),
        unique=True
    )
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))
    function = models.CharField(
        max_length=255,
        verbose_name=_("queue function")
    )
    arguments = JSONField(blank=True, null=True, verbose_name=_('arguments'))
    shop = models.ForeignKey(on_delete=models.CASCADE, to="shuup.Shop",
                             verbose_name=_("shop"), related_name="background_tasks")
    supplier = models.ForeignKey(on_delete=models.CASCADE, to="shuup.Supplier",
                                 verbose_name=_("supplier"), related_name="background_tasks", null=True)
    user = models.ForeignKey(on_delete=models.CASCADE, to=User, verbose_name=_("user"),
                             related_name="background_tasks", null=True)

    class Meta:
        ordering = ("-id",)
        verbose_name = _('background task')
        verbose_name_plural = _('background tasks')


class BackgroundTaskExecutionStatus(Enum):
    RUNNING = 0
    SUCCESS = 1
    ERROR = 2

    class Label:
        RUNNING = _("running")
        SUCCESS = _("success")
        ERROR = _("error")


@python_2_unicode_compatible
class BackgroundTaskExecution(models.Model):
    background_task = models.ForeignKey(on_delete=models.CASCADE, to=BackgroundTask, verbose_name=_("background task"),
                                        related_name="background_task_executions", null=True)
    started_on = models.DateTimeField(verbose_name=_("started on"))
    ended_on = models.DateTimeField(verbose_name=_("ended on"))
    status = EnumIntegerField(
        BackgroundTaskExecutionStatus,
        default=BackgroundTaskExecutionStatus.RUNNING,
        verbose_name=_("status")
    )
    result = JSONField(blank=True, null=True, verbose_name=_('results'))
    error_log = models.TextField(
        verbose_name=_("error log"),
        blank=True,
        null=True
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = _('background task execution')
        verbose_name_plural = _('background task executions')
