# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.utils.translation import activate

from shuup.core.models import AnonymousContact, get_person_contact
from shuup.tasks.admin_module import TaskAdminModule
from shuup.tasks.models import Task, TaskComment, TaskCommentVisibility, TaskStatus, TaskType
from shuup.tasks.utils import create_task
from shuup.testing import factories
from shuup.testing.soup_utils import extract_form_fields
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient

ADMIN_PWD = "admin"


@pytest.mark.django_db
def test_task_admin(admin_user):
    activate("en")
    shop = factories.get_default_shop()

    admin_user.set_password(ADMIN_PWD)
    admin_user.save()
    admin_contact = get_person_contact(admin_user)
    admin_contact.add_to_shop(shop)

    client = SmartClient()
    client.login(username=admin_user.username, password=ADMIN_PWD)

    # Create new task
    new_task_url = reverse("shuup_admin:task.new")
    task_type = TaskType.objects.create(shop=shop, name="my task type")

    assert Task.objects.count() == 0

    # get the form fields
    soup = client.soup(new_task_url)
    payload = extract_form_fields(soup)
    payload.update(
        {"base-name": "My Task", "base-type": task_type.id, "base-assigned_to": admin_contact.id, "base-priority": 10}
    )
    response = client.post(new_task_url, payload)
    assert response.status_code == 302
    assert Task.objects.count() == 1

    task = Task.objects.first()

    # List Tasks
    list_task_url = reverse("shuup_admin:task.list")
    list_data = {"jq": json.dumps({"sort": None, "perPage": 20, "page": 1, "filters": {}})}
    response = client.get(list_task_url, data=list_data)
    assert task.name in response.content.decode("utf-8")

    # Add task comment
    edit_task_url = reverse("shuup_admin:task.edit", kwargs=dict(pk=task.pk))

    assert TaskComment.objects.count() == 0

    soup = client.soup(edit_task_url)
    payload = extract_form_fields(soup)
    payload.update({"comment-body": "Comment here"})
    response = client.post(edit_task_url, payload)
    assert response.status_code == 302
    assert Task.objects.count() == 1
    assert TaskComment.objects.count() == 1

    # Set task status
    assert task.status == TaskStatus.NEW
    response = client.get(edit_task_url)
    assert "Set In Progress" in response.content.decode("utf-8")

    set_task_status_url = reverse("shuup_admin:task.set_status", kwargs=dict(pk=task.pk))
    response = client.post(set_task_status_url, dict(status=TaskStatus.IN_PROGRESS.value))
    assert response.status_code == 302
    task.refresh_from_db()

    assert task.status == TaskStatus.IN_PROGRESS
    response = client.get(edit_task_url)
    assert "Set Completed" in response.content.decode("utf-8")

    response = client.post(set_task_status_url, dict(status=TaskStatus.COMPLETED.value))
    assert response.status_code == 302
    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED

    # invalid status
    response = client.post(set_task_status_url, dict(status=999))
    assert response.status_code == 302
    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED

    # Delete task
    delete_url = reverse("shuup_admin:task.delete", kwargs=dict(pk=task.pk))
    response = client.post(delete_url)
    assert response.status_code == 302
    task.refresh_from_db()
    assert task.status == TaskStatus.DELETED


@pytest.mark.django_db
def test_task_admin_search_dashboard_block(admin_user, rf):
    activate("en")
    shop = factories.get_default_shop()
    task_type = TaskType.objects.create(shop=shop, name="my task type")
    task = create_task(shop, get_person_contact(admin_user), task_type, "Test task")

    request = apply_request_middleware(rf.get("/"), shop=shop, user=admin_user)
    admin_module = TaskAdminModule()
    results = list(admin_module.get_search_results(request, "test"))
    assert len(results) == 0

    dashboard_blocks = list(admin_module.get_dashboard_blocks(request))
    assert len(dashboard_blocks) == 0

    task.assigned_to = get_person_contact(admin_user)
    task.save()
    results = list(admin_module.get_search_results(request, "test"))
    assert len(results) == 1

    dashboard_blocks = list(admin_module.get_dashboard_blocks(request))
    assert len(dashboard_blocks) == 1


@pytest.mark.django_db
def test_task_type_admin(admin_user):
    activate("en")
    shop = factories.get_default_shop()

    admin_user.set_password(ADMIN_PWD)
    admin_user.save()
    admin_contact = get_person_contact(admin_user)
    admin_contact.add_to_shop(shop)

    client = SmartClient()
    client.login(username=admin_user.username, password=ADMIN_PWD)

    # Create new task type
    new_task_type_url = reverse("shuup_admin:task_type.new")
    assert TaskType.objects.count() == 0

    # get the form fields
    soup = client.soup(new_task_type_url)
    payload = extract_form_fields(soup)
    payload.update({"name__en": "My Task Type"})
    response = client.post(new_task_type_url, payload)
    assert response.status_code == 302
    assert TaskType.objects.count() == 1
    task_type = TaskType.objects.first()

    # List task types
    list_task_type_url = reverse("shuup_admin:task_type.list")
    list_data = {"jq": json.dumps({"sort": None, "perPage": 20, "page": 1, "filters": {}})}
    response = client.get(list_task_type_url, data=list_data)
    assert task_type.name in response.content.decode("utf-8")

    # Edit task type
    edit_task_type_url = reverse("shuup_admin:task_type.edit", kwargs=dict(pk=task_type.pk))

    soup = client.soup(edit_task_type_url)
    payload = extract_form_fields(soup)
    payload.update({"name__en": "My Task Type Edited"})
    response = client.post(edit_task_type_url, payload)
    assert response.status_code == 302
