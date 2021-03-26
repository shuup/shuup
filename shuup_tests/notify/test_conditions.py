# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.notify.conditions.simple import BooleanEqual, Empty, IntegerEqual, NonEmpty, TextEqual
from shuup.notify.script import Context


def test_integer_equals():
    ie = IntegerEqual({"v1": {"variable": "v"}, "v2": {"constant": 42}})
    assert ie.test(Context.from_variables(v=42))
    assert ie.test(Context.from_variables(v="42"))
    assert not ie.test(Context.from_variables(v="442"))
    assert not ie.test(Context.from_variables(v=True))


def test_text_equal():
    ie = TextEqual({"v1": {"variable": "v"}, "v2": {"constant": "   Foo   "}})
    assert ie.test(Context.from_variables(v="foo"))
    assert ie.test(Context.from_variables(v="Foo"))
    assert ie.test(Context.from_variables(v="Foo  "))
    assert not ie.test(Context.from_variables(v="faa"))


def test_non_empty():
    ie = NonEmpty({"v": {"variable": "v"}})
    assert ie.test(Context.from_variables(v=True))
    assert not ie.test(Context.from_variables(v=""))
    assert not ie.test(Context.from_variables(v=0))


def test_empty():
    ie = Empty({"v": {"variable": "v"}})
    assert ie.test(Context.from_variables(v=False))
    assert ie.test(Context.from_variables(v=()))
    assert ie.test(Context.from_variables(v=0))
    assert not ie.test(Context.from_variables(v=6))


def test_boolean():
    ie = BooleanEqual({"v1": {"variable": "var1"}, "v2": {"variable": "var2"}})
    assert ie.test(Context.from_variables(var1=False, var2=False))
    assert ie.test(Context.from_variables(var1=False, var2=None))
    assert ie.test(Context.from_variables(var1=True, var2=True))
    assert not ie.test(Context.from_variables(var1=True, var2=False))
    assert not ie.test(Context.from_variables(var1=False, var2=True))

    ie = BooleanEqual({"v1": {"variable": "v"}, "v2": {"constant": None}})
    assert ie.test(Context.from_variables(v=False))
    assert ie.test(Context.from_variables(v=None))
    assert not ie.test(Context.from_variables(v=True))

    ie = BooleanEqual({"v1": {"variable": "v"}, "v2": {"constant": True}})
    assert not ie.test(Context.from_variables(v=False))
    assert not ie.test(Context.from_variables(v=None))
    assert ie.test(Context.from_variables(v=True))
