# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.notify import Event
from shoop_tests.notify.fixtures import get_initialized_test_event, TestEvent


@pytest.mark.django_db
def test_event_init():
    assert get_initialized_test_event().variable_values


def test_extra_vars_fails():
    with pytest.raises(ValueError):
        TestEvent(not_valid=True)


def test_missing_vars_fails():
    with pytest.raises(ValueError):
        TestEvent(just_some_text="Hello")


def test_init_empty_fails():
    with pytest.raises(ValueError):
        Event()

def test_auto_name():
    assert TestEvent.name == "Test Event"
