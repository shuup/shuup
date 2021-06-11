# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import inspect
import json
import logging
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from typing import Any, Optional, Tuple, Union
from uuid import uuid4

from shuup.core.models import BackgroundTask, BackgroundTaskExecution, BackgroundTaskExecutionStatus
from shuup.utils.importing import cached_load, load

LOGGER = logging.getLogger(__name__)


class TaskNotSerializableError(Exception):
    """
    Raised when the task can't be serialized.
    """

    pass


class TaskResult:
    result = None  # type: str
    error_log = None  # type: str

    def __init__(self, result=None, error_log=None):
        if result:
            try:
                json.dumps(result)
            except TypeError:
                raise TaskNotSerializableError("Task result is not serializable as JSON.")

        self.result = result
        self.error_log = error_log


class Task:
    function = ""  # str
    identifier = ""  # str
    stored = False  # bool
    queue = "default"  # str
    kwargs = None  # Optional[Dict[str, Any]]

    def __init__(self, function, identifier=None, stored=False, queue="default", **kwargs):
        """
        :param function: A string that represents the function specification.
            It will be locaded dynamically and executed passing the given kwargs.
            E.g.: `myapp.my_lib.do_domething`

            The function can optionally return a `TaskResult` object which the
            result of the execution. It will be used to store the information
            in the database if the task is stored.

        :param kwargs: Set of parameter to pass to the `function`. The parameters
            must be JSON serializable to support multiple task runners implementations.

        :type function: str
        """
        if not identifier:
            identifier = f"{queue}_{function}_{uuid4().hex}"

        assert isinstance(function, str)

        try:
            json.dumps(kwargs)
        except TypeError:
            raise TaskNotSerializableError("Task kwargs is not serializable as JSON.")

        self.function = function
        self.identifier = identifier
        self.queue = queue
        self.stored = stored
        self.kwargs = kwargs


class TaskRunner:
    def create_task(self, function, stored=False, queue="default", **kwargs) -> Task:
        """
        Create a task to run.

        :type function: str
        """
        raise NotImplementedError()

    def run_task(self, task) -> Optional[TaskResult]:
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

    def create_task(self, function, stored=False, queue="default", task_identifier=None, **kwargs) -> Task:
        task_identifier = task_identifier or f"{queue}_{uuid4().hex}"

        if stored:
            background_data = dict(queue=queue, identifier=task_identifier, function=function, arguments=kwargs)

            if kwargs.get("shop_id"):
                background_data["shop_id"] = kwargs["shop_id"]
            if kwargs.get("supplier_id"):
                background_data["supplier_id"] = kwargs["supplier_id"]
            if kwargs.get("user_id"):
                background_data["user_id"] = kwargs["user_id"]

            BackgroundTask.objects.create(**background_data)

        return Task(function, task_identifier, stored, queue, **kwargs)

    def run_task(self, task) -> Optional[TaskResult]:
        task_identifier = task.identifier
        background_task_execution = None

        background_task = BackgroundTask.objects.filter(identifier=task_identifier).first()
        if background_task:
            background_task_execution = BackgroundTaskExecution.objects.create(task=background_task)

        function = load(task.function)
        task_result = None
        status = BackgroundTaskExecutionStatus.RUNNING

        try:
            arguments = task.kwargs

            # inject the _task_id into the kwargs
            arguments["_task_id"] = task_identifier

            # get the list or args of the function
            args_spec = inspect.getfullargspec(function)

            # go through all kwargs and check if they can be sent to the function
            # and remove those that can't be passed forward
            for arg in list(arguments.keys()):
                if arg not in args_spec.args and arg not in args_spec.kwonlyargs:
                    arguments.pop(arg)

            task_result = function(**arguments)  # type: Union[TaskResult, Any]

            if isinstance(task_result, TaskResult) and task_result.error_log:
                status = BackgroundTaskExecutionStatus.ERROR
            else:
                status = BackgroundTaskExecutionStatus.SUCCESS

        except Exception:
            LOGGER.exception(_("Failed to execute the task"))
            task_result = TaskResult(error_log=_("An unexpeted error occurred."))
            status = BackgroundTaskExecutionStatus.ERROR

        if background_task_execution:
            result = None
            error = None

            if isinstance(task_result, TaskResult):
                result = task_result.result
                error = task_result.error_log
            elif task_result:
                result = str(task_result)

            background_task_execution.finished_on = datetime.now()
            background_task_execution.status = status
            background_task_execution.result = result
            background_task_execution.error_log = error
            background_task_execution.save()

        return task_result


def get_task_runner() -> TaskRunner:
    """
    Returns the task runner configured in settings.

    :rtype: TaskRunner
    """
    return cached_load("SHUUP_TASK_RUNNER")()


def run_task(function, **kwargs) -> Tuple[Task, Any]:
    """
    Runs a function passing the given kwargs using the
    task runner configured in settings.

    Returns a tuple with the task and the result of the task execution

    :type function: str
    """
    task_runner = get_task_runner()
    task = task_runner.create_task(function, **kwargs)
    return task, task_runner.run_task(task)
