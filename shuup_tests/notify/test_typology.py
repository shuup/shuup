# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.notify.base import Binding
from shuup.notify.enums import StepConditionOperator
from shuup.notify.script import Context
from shuup.notify.typology import Enum, Language, Model, Text
from shuup_tests.utils import empty_iterable

from .fixtures import ATestEvent


def test_simple_type_matching():
    assert Binding("x", type=Language).get_matching_types(ATestEvent.variables) == {"order_language"}


def test_text_type_matches_all():
    assert Binding("x", type=Text).get_matching_types(ATestEvent.variables) == set(ATestEvent.variables.keys())


def test_model_type_matching():
    assert empty_iterable(Binding("x", type=Model("shuup.Contact")).get_matching_types(ATestEvent.variables))
    assert Binding("x", type=Model("shuup.Order")).get_matching_types(ATestEvent.variables) == {"order"}


def test_enum_type():
    enum_type = Enum(StepConditionOperator)
    assert enum_type.unserialize(StepConditionOperator.ANY) == StepConditionOperator.ANY
    assert enum_type.unserialize("any") == StepConditionOperator.ANY
    assert not enum_type.unserialize("herp")


def test_binding_fallthrough():
    ctx = Context.from_variables()
    b = Binding("x", default="foo")
    assert b.get_value(ctx, {"variable": "var"}) == "foo"
    assert b.get_value(ctx, {}) == "foo"
