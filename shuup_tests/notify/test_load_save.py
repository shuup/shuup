# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.encoding import force_text

from shuup.notify.models import Script
from shuup.notify.script import Step
from shuup.testing import factories
from shuup_tests.notify.fixtures import TEST_STEP_DATA, ATestEvent


@pytest.mark.django_db
def test_load_save():
    sc = Script(event_identifier=ATestEvent.identifier, name="Test Script", shop=factories.get_default_shop())
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
