# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.notify.actions.debug import SetDebugFlag
from shuup.notify.conditions.simple import NonEmpty
from shuup.notify.enums import StepConditionOperator
from shuup.notify.script import Context, Step

from .fixtures import get_test_script


def test_basic_exec():
    script = get_test_script()

    # `en` is not in the conditions
    context = Context.from_variables(order_language="en")
    script.execute(context)
    assert not context.get("success")

    # `fi` is matched by the first condition and cond_op is 'or'
    context = Context.from_variables(order_language="fi")
    script.execute(context)
    assert context.get("success")

    # `ja` is matched by the other condition, and cond_op is 'or'
    context = Context.from_variables(order_language="ja")
    script.execute(context)
    assert context.get("success")


def test_disabled_steps():
    script = get_test_script()
    steps = script.get_steps()
    steps[0].enabled = False
    script.set_steps(steps)
    # Disabled steps don't run
    context = Context.from_variables()
    script.execute(context)
    assert not context.get("success")


def test_conditionless_step_executes():
    step = Step(actions=[SetDebugFlag({})])
    context = Context()
    step.execute(context)
    assert context.get("debug")


@pytest.mark.parametrize("cond_op", list(StepConditionOperator))
def test_condops(cond_op):
    step = Step(
        cond_op=cond_op,
        conditions=[
            NonEmpty({"v": {"variable": "a"}}),
            NonEmpty({"v": {"variable": "b"}}),
        ],
        actions=[SetDebugFlag({})],
    )
    context = Context.from_variables(a=True, b=False)
    step.execute(context)
    if cond_op == StepConditionOperator.ALL:
        assert not context.get("debug")
    elif cond_op == StepConditionOperator.ANY:
        assert context.get("debug")
    elif cond_op == StepConditionOperator.NONE:
        assert not context.get("debug")
    else:
        raise ValueError("Error! Unexpected cond_op %r." % cond_op)


def test_none_condop():
    step = Step(
        cond_op=StepConditionOperator.NONE,
        conditions=[
            NonEmpty({"v": {"variable": "a"}}),
            NonEmpty({"v": {"variable": "b"}}),
        ],
        actions=[SetDebugFlag({})],
    )
    context = Context.from_variables(a=False, b=False)
    step.execute(context)
    assert context.get("debug")
