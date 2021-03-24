# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.db.models import Q
from django.db.transaction import atomic
from django.forms.models import ModelForm
from django.http.response import HttpResponseNotAllowed, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView
from django.views.generic.detail import BaseDetailView

from shuup.admin.forms.widgets import QuickAddRelatedObjectSelect
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import PostActionButton, get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Contact, get_person_contact
from shuup.tasks.models import Task, TaskComment, TaskStatus, TaskType
from shuup.utils.analog import LogEntryKind
from shuup.utils.django_compat import reverse_lazy
from shuup.utils.form_group import FormGroup
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class QuickAddTaskTypeSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:task_type.new")


class TaskTypeForm(MultiLanguageModelForm):
    class Meta:
        model = TaskType
        exclude = ("shop",)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(TaskTypeForm, self).__init__(*args, **kwargs)

    def save(self, **kwargs):
        if not self.instance.pk:
            self.instance.shop = get_shop(self.request)
        return super(TaskTypeForm, self).save(**kwargs)


class TaskForm(ModelForm):
    class Meta:
        model = Task
        exclude = ("shop", "created_on", "modified_on", "status", "completed_on", "completed_by", "creator")
        widgets = {"type": QuickAddTaskTypeSelect(editable_model="shuup_tasks.TaskType")}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(TaskForm, self).__init__(*args, **kwargs)

        shop = get_shop(self.request)
        self.fields["assigned_to"].queryset = Contact.objects.filter(
            Q(shops=shop) | Q(id__in=shop.staff_members.values_list("id"))
        ).distinct()
        self.fields["assigned_to"].widget.editable_model = "shuup.Contact"

    def save(self, **kwargs):
        is_new = not self.instance.pk
        old_assigned = None
        if not is_new:
            old_assigned = Task.objects.get(id=self.instance.pk).assigned_to

        if is_new:
            self.instance.creator = get_person_contact(self.request.user)
            self.instance.shop = get_shop(self.request)

        result = super(TaskForm, self).save(**kwargs)

        if not is_new and old_assigned != self.instance.assigned_to:
            self.instance.add_log_entry(
                _("Changed assigment from {from_contact_name} to {to_contact_name}.").format(
                    **dict(from_contact_name=old_assigned, to_contact_name=self.instance.assigned_to)
                ),
                kind=LogEntryKind.EDIT,
            )

        return result


class TaskCommentForm(ModelForm):
    class Meta:
        model = TaskComment
        exclude = ("task", "created_on", "modified_on", "author")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.task = kwargs.pop("task")
        super(TaskCommentForm, self).__init__(*args, **kwargs)

    def save(self, **kwargs):
        if not self.instance.pk:
            self.instance.task = self.task
            self.instance.author = get_person_contact(self.request.user)
        return super(TaskCommentForm, self).save(**kwargs)


class BaseTaskViewMixin(object):
    def get_queryset(self):
        tasks = Task.objects.for_shop(get_shop(self.request))
        if not self.request.user.is_superuser:
            tasks = tasks.exclude(status=TaskStatus.DELETED)
        return tasks


class TaskTypeEditView(CreateOrUpdateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = "shuup/admin/tasks/task_type_edit.jinja"
    context_object_name = "task_type"

    def get_queryset(self):
        return TaskType.objects.filter(shop=get_shop(self.request))

    def get_form_kwargs(self, **kwargs):
        args = super(TaskTypeEditView, self).get_form_kwargs(**kwargs)
        args["request"] = self.request
        return args


class TaskEditView(BaseTaskViewMixin, CreateOrUpdateView):
    model = Task
    template_name = "shuup/admin/tasks/task_edit.jinja"
    context_object_name = "task"
    fields = ()

    def get_form_class(self):
        return None

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        obj = self.get_object()
        delete_url = reverse_lazy("shuup_admin:task.delete", kwargs={"pk": obj.pk}) if obj.pk else None
        toolbar = get_default_edit_toolbar(self, save_form_id, delete_url=delete_url)

        if obj and obj.pk:
            if obj.status == TaskStatus.NEW:
                toolbar.append(
                    PostActionButton(
                        post_url=reverse_lazy("shuup_admin:task.set_status", kwargs=dict(pk=obj.pk)),
                        icon="fa fa-check",
                        name="status",
                        value=TaskStatus.IN_PROGRESS.value,
                        text=_("Set In Progress"),
                        extra_css_class="btn-success",
                    )
                )
            if obj.status == TaskStatus.IN_PROGRESS:
                toolbar.append(
                    PostActionButton(
                        post_url=reverse_lazy("shuup_admin:task.set_status", kwargs=dict(pk=obj.pk)),
                        icon="fa fa-check",
                        name="status",
                        value=TaskStatus.COMPLETED.value,
                        text=_("Set Completed"),
                        extra_css_class="btn-success",
                    )
                )
        return toolbar

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        instance = kwargs.pop("instance", None)
        form_group = FormGroup(**kwargs)
        form_group.add_form_def(name="base", form_class=TaskForm, kwargs=dict(instance=instance, request=self.request))
        if self.object.pk:
            form_group.add_form_def(
                name="comment",
                form_class=TaskCommentForm,
                kwargs=dict(request=self.request, task=instance),
                required=False,
            )
        return form_group

    @atomic
    def save_form(self, form):
        is_new = not self.object.pk
        form.forms["base"].save()
        if not is_new and form.forms["comment"].cleaned_data.get("body"):
            form.forms["comment"].save()

    def get_context_data(self, **kwargs):
        context = super(TaskEditView, self).get_context_data(**kwargs)
        comments = []
        task = self.get_object()
        if task:
            comments = task.comments.for_contact(get_person_contact(self.request.user)).order_by("created_on")
        context["comments"] = comments
        return context


class TaskDeleteView(BaseTaskViewMixin, DeleteView):
    model = Task
    success_url = reverse_lazy("shuup_admin:task.list")


class TaskSetStatusView(BaseTaskViewMixin, BaseDetailView):
    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(permitted_methods=["post"])

    def post(self, request, *args, **kwargs):
        status = int(request.POST.get("status", 0))
        obj = self.get_object()
        redirect_url = reverse_lazy("shuup_admin:task.edit", kwargs=dict(pk=obj.pk))
        possible_status = [TaskStatus.COMPLETED.value, TaskStatus.IN_PROGRESS.value]

        if not status or status not in possible_status:
            messages.error(request, _("Invalid status."))
            return HttpResponseRedirect(redirect_url)

        if status == TaskStatus.COMPLETED.value:
            obj.set_completed(get_person_contact(request.user))
        elif status == TaskStatus.IN_PROGRESS.value:
            obj.set_in_progress()

        obj.save()
        messages.success(request, _("Status changed."))
        return HttpResponseRedirect(redirect_url)
