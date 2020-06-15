# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

from shuup.utils.importing import cached_load, load


class TaskNotSerializableError(Exception):
    """
    Raised when the task can't be serialized.
    """
    pass


class Task:
    function = ""       # type: str
    kwargs = None       # type: Optional[Dict[str, Any]]

    def __init__(self, function, **kwargs):
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
        self.kwargs = kwargs


class TaskRunner:
    def create_task(self, function, **kwargs):
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

    def create_task(self, function, **kwargs):
        return Task(function, **kwargs)

    def run_task(self, task):
        function = load(task.function)
        return function(**task.kwargs)


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
