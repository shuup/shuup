# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.notify.base import Binding
from shoop.notify.enums import StepConditionOperator
from shoop.notify.script import Context
from shoop.notify.typology import Enum, Language, Model, Text
from shoop_tests.utils import empty_iterable

from .fixtures import TestEvent


def test_simple_type_matching():
    assert Binding("x", type=Language).get_matching_types(TestEvent.variables) == {"order_language"}


def test_text_type_matches_all():
    assert Binding("x", type=Text).get_matching_types(TestEvent.variables) == set(TestEvent.variables.keys())


def test_model_type_matching():
    assert empty_iterable(Binding("x", type=Model("shoop.Contact")).get_matching_types(TestEvent.variables))
    assert Binding("x", type=Model("shoop.Order")).get_matching_types(TestEvent.variables) == {"order"}


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
