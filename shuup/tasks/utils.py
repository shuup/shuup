# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic


def create_task(shop, creator, task_type, task_name, comment=None, **kwargs):
    from shuup.tasks.models import Task

    with atomic():
        task = Task(creator=creator, shop=shop, type=task_type, name=task_name, **kwargs)
        task.full_clean()
        task.save()
        if comment:
            task.comment(creator, comment)
        return task
