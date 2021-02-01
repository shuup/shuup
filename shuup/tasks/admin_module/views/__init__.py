# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from .edit import (
    TaskDeleteView, TaskEditView, TaskSetStatusView, TaskTypeEditView
)
from .list import TaskListView, TaskTypeListView

__all__ = [
    "TaskEditView",
    "TaskListView",
    "TaskDeleteView",
    "TaskSetStatusView",
    "TaskTypeListView",
    "TaskTypeEditView"
]
