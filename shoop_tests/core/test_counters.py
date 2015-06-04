# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ObjectDoesNotExist
import pytest
from shoop.core.models.counters import CounterType, Counter


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
