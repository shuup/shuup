# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.utils.analog import define_log_model, LogEntryKind


class TaskStatus(Enum):
    NEW = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    DELETED = 4

    class Labels:
        NEW = _("New")
        IN_PROGRESS = _("In progress")
        COMPLETED = _("Completed")
        DELETED = _("Deleted")


class TaskCommentVisibility(Enum):
    PUBLIC = 1
    STAFF_ONLY = 2
    ADMINS_ONLY = 3

    class Labels:
        PUBLIC = _("Public")
        STAFF_ONLY = _("Staff Only")
        ADMINS_ONLY = _("Admins Only")


@python_2_unicode_compatible
class TaskType(TranslatableModel):
    identifier = InternalIdentifierField(unique=False, blank=True, null=True, editable=True)
    shop = models.ForeignKey("shuup.Shop", verbose_name=_("shop"), related_name="task_types")
    translations = TranslatedFields(
        name=models.TextField(verbose_name=_("name"))
    )

    class Meta:
        unique_together = ("shop", "identifier")
        verbose_name = _('task type')
        verbose_name_plural = _('task types')

    def __str__(self):
        return self.name


class TaskQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status=TaskStatus.COMPLETED)

    def in_progress(self):
        return self.filter(status=TaskStatus.IN_PROGRESS)

    def is_new(self):
        return self.filter(tatus=TaskStatus.NEW)

    def for_shop(self, shop):
        return self.filter(shop=shop)

    def delete(self):
        self.update(status=TaskStatus.DELETED)

    def assigned_to(self, contact):
        return self.filter(assigned_to=contact)


@python_2_unicode_compatible
class Task(models.Model):
    shop = models.ForeignKey("shuup.Shop", verbose_name=_("shop"), related_name="tasks")
    name = models.CharField(verbose_name=_("name"), max_length=60)
    type = models.ForeignKey(TaskType, verbose_name=_("task type"), related_name="tasks")
    status = EnumIntegerField(TaskStatus, default=TaskStatus.NEW, verbose_name=_("status"))
    priority = models.PositiveIntegerField(default=0, verbose_name=_("priority"), db_index=True)
    creator = models.ForeignKey(
        "shuup.Contact",
        blank=True,
        null=True,
        related_name="creted_tasks",
        verbose_name=_("creator")
    )
    assigned_to = models.ForeignKey(
        "shuup.Contact",
        blank=True,
        null=True,
        related_name="assigned_tasks",
        verbose_name=_("assigned to")
    )
    completed_by = models.ForeignKey(
        "shuup.Contact",
        blank=True,
        null=True,
        related_name="completed_tasks",
        verbose_name=_("completed by")
    )
    completed_on = models.DateTimeField(verbose_name=_("completed on"), null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_("modified on"))

    objects = TaskQuerySet.as_manager()

    def __str__(self):
        return self.name

    def assign(self, user):
        self.assigned_to = user
        self.status = TaskStatus.IN_PROGRESS
        self.save()

    def delete(self):
        self.status = TaskStatus.DELETED
        self.save(update_fields=["status"])
        self.add_log_entry("Deleted.", kind=LogEntryKind.DELETION)

    def comment(self, contact, comment, visibility=TaskCommentVisibility.PUBLIC):
        comment = TaskComment(task=self, author=contact, body=comment, visibility=visibility)
        comment.full_clean()
        comment.save()
        return comment

    def set_in_progress(self):
        self.status = TaskStatus.IN_PROGRESS
        self.add_log_entry("In progress.", kind=LogEntryKind.EDIT)
        self.save()

    def set_completed(self, contact):
        self.completed_by = contact
        self.completed_on = now()
        self.status = TaskStatus.COMPLETED
        self.add_log_entry("Completed.", kind=LogEntryKind.EDIT)
        self.save()

    def get_completion_time(self):
        if self.completed_on:
            return (self.completed_on - self.created_on)


class TaskCommentQuerySet(models.QuerySet):
    def for_contact(self, contact):
        visibility_filters = Q(visibility=TaskCommentVisibility.PUBLIC)

        if hasattr(contact, "user") and contact.user:
            # see everything
            if contact.user.is_superuser:
                visibility_filters = Q()

            elif contact.user.is_staff:
                visibility_filters |= Q(
                    visibility=TaskCommentVisibility.STAFF_ONLY,
                    task__shop__staff_members=contact.user
                )

        return self.filter(visibility_filters).distinct()


class TaskComment(models.Model):
    task = models.ForeignKey(Task, verbose_name=_("task"), related_name="comments")
    author = models.ForeignKey(
        "shuup.Contact",
        blank=True, null=True,
        related_name="task_comments",
        verbose_name=_("author")
    )
    visibility = EnumIntegerField(
        TaskCommentVisibility,
        default=TaskCommentVisibility.PUBLIC,
        db_index=True,
        verbose_name=_("visibility")
    )
    body = models.TextField(verbose_name=_("body"))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_("modified on"))

    objects = TaskCommentQuerySet.as_manager()

    def reply(self, contact, body):
        comment = TaskComment(task=self.task, comment_author=contact, body=body)
        comment.full_clean()
        comment.save()
        return comment

    def as_html(self):
        return mark_safe(force_text(self.body))

    def can_see(self, user):
        is_admin = user.is_superuser
        is_staff = bool(user.is_staff and user in self.task.shop.staff_members.all())

        if not (is_admin or is_staff):
            return (self.visibility == TaskCommentVisibility.PUBLIC)
        elif not is_admin:
            return (
                self.visibility == TaskCommentVisibility.PUBLIC or
                self.visibility == TaskCommentVisibility.STAFF_ONLY
            )

        return True


TaskLogEntry = define_log_model(Task)
