# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import BackgroundTask
from shuup.core.tasks import TaskNotSerializableError, run_task
from shuup.testing import factories


def test_run_task():
    task, result = run_task("shuup.utils.text.snake_case", value="test ing")
    assert result == "test_ing"
    assert task.identifier


def test_run_task_with_exception():
    _, result = run_task("shuup.utils.text.identifierify", value=3)
    assert result.error_log

    with pytest.raises(TaskNotSerializableError):
        run_task("shuup.utils.text.identifierify", value=object)


@pytest.mark.django_db
def test_run_task_with_objects(admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier(shop)

    task, result = run_task(
        "shuup.utils.text.snake_case",
        value="test ing",
        stored=True,
        queue="random",
        shop_id=shop.pk,
        supplier_id=supplier.pk,
        user_id=admin_user.pk,
    )
    bg_task = BackgroundTask.objects.get(identifier=task.identifier)
    assert bg_task.supplier == supplier
    assert bg_task.shop == shop
    assert bg_task.user == admin_user
