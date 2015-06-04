# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.encoding import force_text
import pytest
from shoop.notify.models import Script
from shoop.notify.script import Step
from shoop_tests.notify.fixtures import TEST_STEP_DATA, TestEvent


@pytest.mark.django_db
def test_load_save():
    sc = Script(event_identifier=TestEvent.identifier, name="Test Script")
    assert force_text(sc) == "Test Script"
    sc.set_serialized_steps(TEST_STEP_DATA)
    sc.save()
    sc = Script.objects.get(pk=sc.pk)

    first_step = sc.get_steps()[0]
    first_step_data = TEST_STEP_DATA[0]
    step_from_data = Step.unserialize(first_step_data)
    data_from_step = first_step.serialize()

    assert data_from_step == first_step_data
    assert first_step == step_from_data
