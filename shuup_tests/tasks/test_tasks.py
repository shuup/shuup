# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import AnonymousContact, get_person_contact
from shuup.tasks.models import Task, TaskComment, TaskCommentVisibility, TaskStatus, TaskType
from shuup.tasks.utils import create_task
from shuup.testing import factories


@pytest.mark.django_db
def test_basic_tasks(admin_user):
    shop = factories.get_default_shop()
    contact = factories.create_random_person(shop=shop)
    # task gets created
    text = "derpy hooves"
    task_type = TaskType.objects.create(name="Request", shop=shop)
    task = create_task(shop, contact, task_type, "my task", comment=text)

    assert Task.objects.count() == 1
    assert TaskComment.objects.count() == 1
    assert TaskComment.objects.first().author == contact
    assert contact.task_comments.count() == 1
    assert not task.assigned_to
    assert task.status == TaskStatus.NEW

    # someone handles it
    admin_contact = factories.create_random_person()
    admin_contact.user = admin_user
    admin_contact.save()
    task.assign(admin_contact)
    task.refresh_from_db()

    assert task.assigned_to == admin_contact
    assert task.status == TaskStatus.IN_PROGRESS

    comment_text = "this being handled now"
    task.comment(admin_contact, comment_text)

    task.refresh_from_db()

    assert task.comments.count() == 2
    assert task.comments.last().body == comment_text

    assert TaskComment.objects.count() == 2

    task.set_in_progress()
    task.refresh_from_db()
    assert task.status == TaskStatus.IN_PROGRESS

    task.set_completed(admin_contact)
    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED

    assert task.completed_on
    assert task.completed_by == admin_contact


def test_comment_visibility(admin_user):
    shop = factories.get_default_shop()

    admin_contact = get_person_contact(admin_user)

    staff_user = factories.create_random_user("en", is_staff=True)
    staff_contact = get_person_contact(staff_user)
    shop.staff_members.add(staff_user)

    normal_user = factories.create_random_user("en")
    normal_contact = get_person_contact(normal_user)

    task_type = TaskType.objects.create(name="Request", shop=shop)
    task = create_task(shop, admin_contact, task_type, "my task")

    task.comment(admin_contact, "This is only visibile for super users", TaskCommentVisibility.ADMINS_ONLY)
    task.comment(staff_contact, "This is only visibile for staff only", TaskCommentVisibility.STAFF_ONLY)
    task.comment(normal_contact, "This is visibile for everyone", TaskCommentVisibility.PUBLIC)

    # admin see all comments
    assert task.comments.for_contact(admin_contact).count() == 3
    # staff see all public + staff only
    assert task.comments.for_contact(staff_contact).count() == 2
    # normal contact see all public
    assert task.comments.for_contact(normal_contact).count() == 1
    # anonymous contact see all public
    assert task.comments.for_contact(AnonymousContact()).count() == 1
