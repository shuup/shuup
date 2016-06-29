# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.notify.actions.order import AddOrderLogEntry
from shuup.notify.enums import StepNext
from shuup.notify.models import Script
from shuup.notify.script import Step
from shuup_tests.notify.fixtures import get_initialized_test_event


@pytest.mark.django_db
def test_run():
    event = get_initialized_test_event()
    step = Step(actions=[AddOrderLogEntry({
        "order": {"variable": "order"},
        "message": {"constant": "It Works."},
        "message_identifier": {"constant": "test_run"},
    })], next=StepNext.STOP)
    script = Script(event_identifier=event.identifier, name="Test Script")
    script.set_steps([step])
    script.save()
    event.run()
    # The script is disabled by default, of course it won't run
    assert not event.variable_values["order"].log_entries.filter(identifier="test_run").exists()

    # Let's try that again.
    script.enabled = True
    script.save()
    event.run()
    assert event.variable_values["order"].log_entries.filter(identifier="test_run").exists()
    script.delete()
