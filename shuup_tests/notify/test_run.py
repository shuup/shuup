# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.notify.actions.order import AddOrderLogEntry
from shuup.notify.enums import StepNext
from shuup.notify.models import Script
from shuup.notify.script import Step
from shuup.testing import factories
from shuup_tests.notify.fixtures import get_initialized_test_event


@pytest.mark.django_db
def test_run():
    event = get_initialized_test_event()
    step = Step(
        actions=[
            AddOrderLogEntry(
                {
                    "order": {"variable": "order"},
                    "message": {"constant": "It Works."},
                    "message_identifier": {"constant": "test_run"},
                }
            )
        ],
        next=StepNext.STOP,
    )
    script = Script(event_identifier=event.identifier, name="Test Script", shop=factories.get_default_shop())
    script.set_steps([step])
    script.save()
    event.run(factories.get_default_shop())
    # The script is disabled by default, of course it won't run
    assert not event.variable_values["order"].log_entries.filter(identifier="test_run").exists()

    # Let's try that again.
    script.enabled = True
    script.save()
    event.run(factories.get_default_shop())
    assert event.variable_values["order"].log_entries.filter(identifier="test_run").exists()
    script.delete()


@pytest.mark.django_db
def test_run_multishop():
    shop1 = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")
    event = get_initialized_test_event()
    step = Step(
        actions=[
            AddOrderLogEntry(
                {
                    "order": {"variable": "order"},
                    "message": {"constant": "It Works."},
                    "message_identifier": {"constant": "test_run"},
                }
            )
        ],
        next=StepNext.STOP,
    )
    script = Script(event_identifier=event.identifier, name="Test Script", shop=shop2, enabled=True)
    script.set_steps([step])
    script.save()

    # runs for shop1 - no script exists
    event.run(shop1)
    assert not event.variable_values["order"].log_entries.filter(identifier="test_run").exists()

    # run for shop2 - ok
    event.run(shop2)
    assert event.variable_values["order"].log_entries.filter(identifier="test_run").exists()
    script.delete()
