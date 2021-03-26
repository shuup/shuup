# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging
import six
from django.db.models.query import QuerySet

from shuup.notify.base import Action, Condition
from shuup.notify.enums import StepConditionOperator, StepNext
from shuup.utils.analog import BaseLogEntry


def none(conditions):
    return not any(conditions)


cond_op_to_func_map = {
    StepConditionOperator.ALL: all,
    StepConditionOperator.NONE: none,
    StepConditionOperator.ANY: any,
}


class Step(object):
    def __init__(
        self, conditions=(), actions=(), next=StepNext.CONTINUE, cond_op=StepConditionOperator.ALL, enabled=True
    ):
        self._conditions = conditions
        self._actions = actions
        self._next = StepNext(next)
        self._enabled = bool(enabled)
        self._cond_op = StepConditionOperator(cond_op)

    def execute(self, context):
        if not self._enabled:
            return StepNext.CONTINUE

        cond_op_func = cond_op_to_func_map[self._cond_op]

        if cond_op_func(cond.test(context) for cond in self._conditions):
            for action in self._actions:
                action.execute(context)
            return self._next
        return StepNext.CONTINUE

    def serialize(self):
        return {
            "conditions": [cond.serialize() for cond in self._conditions],
            "actions": [action.serialize() for action in self._actions],
            "next": self._next.value,
            "cond_op": self._cond_op.value,
            "enabled": self._enabled,
        }

    @classmethod
    def unserialize(cls, step_data):
        kwargs = {
            "conditions": [Condition.unserialize(cond) for cond in step_data.get("conditions", ())],
            "actions": [Action.unserialize(action) for action in step_data.get("actions", ())],
        }
        if "next" in step_data:
            kwargs["next"] = StepNext(step_data["next"])
        if "cond_op" in step_data:
            kwargs["cond_op"] = StepConditionOperator(step_data["cond_op"])
        if "enabled" in step_data:
            kwargs["enabled"] = bool(step_data["enabled"])
        return cls(**kwargs)

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        fields = ("_next", "_enabled", "_cond_op", "_conditions", "_actions")
        return all(getattr(self, field) == getattr(other, field) for field in fields)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = bool(value)


CONTEXT_LOGGER = logging.Logger("%s.Context" % __name__)


class Context(object):
    def __init__(self, variables=None, shop=None, event_identifier=None):
        if not variables:
            variables = {}
        self.event_identifier = event_identifier
        self.shop = shop
        self._variables = dict(variables)
        self._logger = CONTEXT_LOGGER  # This object could be replaced if required
        self._log_target = None

    @classmethod
    def from_variables(cls, shop=None, event_identifier=None, **variables):
        """
        Create Context from variables.

        :param event_identifier: identifier for shuup.notify event type
        :rtype: shuup.notify.script.Context
        """
        return cls(variables, shop, event_identifier)

    @classmethod
    def from_event(cls, event, shop=None):
        """
        Create Context from event.

        :type event: shuup.notify.Event
        :type shop: shuup.Shop
        :rtype: shuup.notify.script.Context
        """
        ctx = cls(event.variable_values, shop, event.identifier)
        ctx._log_target = event.log_target
        return ctx

    def get(self, name, default=None):
        return self._variables.get(six.text_type(name), default)

    def set(self, name, value):
        self._variables[six.text_type(name)] = value

    def get_variables(self):
        return self._variables.copy()

    def log(self, level, msg, *args, **kwargs):
        """
        Log a message with the context's logger (not the log target).
        This may be an useful debugging tool.

        The parameters are the same as for `logging.Logger.log()`.
        """
        self._logger.log(level, msg, *args, **kwargs)

    def add_log_entry_on_log_target(self, message, identifier, **kwargs):
        """
        Add a log entry on the context's log target.

        The kwargs are passed to the target's `add_log_entry` method.

        If no log target exists or if it has no `add_log_entry` method, this method does
        nothing.

        :param message: The message text.
        :type message: str
        :param identifier: The message identifier. Unlike with `add_log_entry`, this is required.
        :type identifier: str
        :param kwargs: Other kwargs to pass to `add_log_entry`
        :type kwargs: dict
        """
        if not identifier:
            raise ValueError("Error! `identifier` is required for script logging.")

        if not self._log_target:
            return

        add_log_entry = getattr(self._log_target, "add_log_entry", None)
        if not callable(add_log_entry):
            return

        kwargs["message"] = message
        kwargs["identifier"] = identifier
        return add_log_entry(**kwargs)

    @property
    def log_entry_queryset(self):
        log_entries = getattr(self._log_target, "log_entries", None)
        if log_entries is None:
            return QuerySet(BaseLogEntry).none()  # `BaseLogEntry` doesn't have `objects` as it's abstract
        return log_entries.all()
