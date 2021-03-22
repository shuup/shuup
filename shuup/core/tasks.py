# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from datetime import datetime
import json
from uuid import uuid4

from shuup.core.models import BackgroundTask, Shop, Supplier, BackgroundTaskExecution
from shuup.utils.importing import cached_load, load


class TaskNotSerializableError(Exception):
    """
    Raised when the task can't be serialized.
    """

    pass


class Task:
    function = ""  # str
    identifier = ""  # str
    stored = False  # bool
    queue = "default"  # str
    kwargs = None  # Optional[Dict[str, Any]]

    def __init__(self, function, identifier, stored=False, queue="default", **kwargs):
        """
        :param function: A string that represents the function specification.
            It will be locaded dynamically and executed passing the given kwargs.
            E.g.: `myapp.my_lib.do_domething`

        :param kwargs: Set of parameter to pass to the `function`. The parameters
            must be JSON serializable to support multiple task runners implementations.

        :type function: str
        """
        assert isinstance(function, str)

        try:
            json.dumps(kwargs)
        except TypeError:
            raise TaskNotSerializableError("Task kwargs is not serializable.")

        self.function = function
        self.identifier = identifier
        self.queue = queue
        self.stored = stored
        self.kwargs = kwargs


class TaskRunner:
    def create_task(self, function, stored=False, queue="default", **kwargs):
        """
        Create a task to run.

        :type function: str
        """
        raise NotImplementedError()

    def run_task(self, task):
        """
        Run the given task.

        :type task: Task
        """
        raise NotImplementedError()


class DefaultTaskRunner(TaskRunner):
    """
    The default implementation of a task runner.

    This task runner will execute the tasks received synchronously.
    """

    def create_task(self, function, stored=False, queue="default", **kwargs):
        task_identifier = uuid4().hex
        if stored:

            background_data = {"queue": queue, "identifier": task_identifier, "function": function}

            if "shop_id" in kwargs and kwargs["shop_id"]:
                background_data["shop"] = Shop.objects.filter(kwargs["shop_id"]).first()
            if "supplier_id" in kwargs and kwargs["supplier_id"]:
                supplier = Supplier.objects.filter(kwargs).first()
                background_data["supplier"] = supplier

            BackgroundTask.objects.create(
                queue=queue,
                identifier=task_identifier,
                function=function,
            )
        return Task(function, task_identifier, stored, queue, **kwargs)

    def run_task(self, task):
        task_identifier = task.identifier

        bg_task_qs = BackgroundTask.objects.filter(identifier=task_identifier)
        if bg_task_qs.exists():
            bg_task = bg_task_qs.first()
            started_on = datetime.now()
            bg_task_exec = BackgroundTaskExecution.objects.create(
                started_on=started_on, background_task=bg_task
            )

        function = load(task.function)
        success = True
        try:
            result = function(**task.kwargs)
        except Exception as e:
            success = False
            result = e
        finally:
            if bg_task_exec:
                self.update_task_execution(bg_task_exec, success, result)

        return result

    def update_task_execution(
        self, task_exec: BackgroundTaskExecution, success, result, *args, **kwargs
    ):
        ended_on = datetime.now()
        task_exec.ended_on = ended_on
        if success:
            task_exec.result = result
        else:
            task_exec.error_log = result
        task_exec.save()


def get_task_runner():
    """
    Returns the task runner configured in settings.

    :rtype: TaskRunner
    """
    return cached_load("SHUUP_TASK_RUNNER")()


def run_task(function, **kwargs):
    """
    Runs a function passing the given kwargs using the
    task runner configured in settings.

    :type function: str
    """
    task_runner = get_task_runner()
    task = task_runner.create_task(function, **kwargs)
    return task_runner.run_task(task)
