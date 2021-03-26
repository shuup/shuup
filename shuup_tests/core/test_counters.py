# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ObjectDoesNotExist

from shuup.core.models import Counter, CounterType


@pytest.mark.django_db
def test_counters():
    for counter_id in (CounterType.ORDER_REFERENCE,):
        try:
            initial = Counter.objects.get(id=CounterType.ORDER_REFERENCE).value
        except ObjectDoesNotExist:
            initial = 0

        last = None
        for x in range(51):
            last = Counter.get_and_increment(counter_id)

        assert last == initial + 50
        assert Counter.objects.get(id=CounterType.ORDER_REFERENCE).value == initial + 51
