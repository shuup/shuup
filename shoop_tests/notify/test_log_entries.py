# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.notify import Context
from shoop_tests.notify.fixtures import get_initialized_test_event


@pytest.mark.django_db
def test_log_entries():
    event = get_initialized_test_event()
    ctx = Context.from_event(event)
    order = ctx.get("order")
    n_log_entries = ctx.log_entry_queryset.count()
    ctx.add_log_entry_on_log_target("blap", "blorr")
    order.add_log_entry("blep")
    assert ctx.log_entry_queryset.count() == n_log_entries + 2  # they got added
    assert order.log_entries.last().message == "blep"  # it's what we added
    assert ctx.log_entry_queryset.last().message == "blep"  # from this perspective too


@pytest.mark.django_db
@pytest.mark.parametrize("target_obj", (None, object()))
def test_log_entry_on_unloggable_object(target_obj):
    event = get_initialized_test_event()
    event.variable_values["order"] = target_obj  # invalidate log target _before_ creating context
    ctx = Context.from_event(event)
    n_log_entries = ctx.log_entry_queryset.count()
    ctx.add_log_entry_on_log_target("blap", "blorr")
    assert ctx.log_entry_queryset.count() == n_log_entries  # couldn't add :(
