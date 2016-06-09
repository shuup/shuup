# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import hashlib

import pytest
from django.test import override_settings

from shuup.core.models._order_utils import (
    get_order_identifier, get_reference_number
)
from shuup.testing.factories import create_empty_order


def custom_refno_gen(order):
    return "3030%08d" % (order.pk << 2)


def custom_ident_gen(order):
    return hashlib.sha1(str(order.pk).encode("utf-8")).hexdigest()


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["unique", "running", "shop_running"])
def test_refno_generation(method):
    for attempt in range(10):
        with override_settings(SHUUP_REFERENCE_NUMBER_METHOD=method):
            order = create_empty_order()
            order.save()
            assert order.reference_number
        with pytest.raises(ValueError):
            get_reference_number(order)


@pytest.mark.django_db
def test_custom_refno_generation():
    methods = (
        custom_refno_gen,
        "%s.%s" % (__name__, custom_refno_gen.__name__)
    )
    for method in methods:
        with override_settings(SHUUP_REFERENCE_NUMBER_METHOD=method):
            order = create_empty_order()
            order.save()
            assert order.reference_number == custom_refno_gen(order)
        with pytest.raises(ValueError):
            get_reference_number(order)


@pytest.mark.django_db
def test_custom_ident_generation():
    methods = (
        custom_ident_gen,
        "%s.%s" % (__name__, custom_ident_gen.__name__)
    )
    for method in methods:
        with override_settings(SHUUP_ORDER_IDENTIFIER_METHOD=method):
            order = create_empty_order()
            order.save()
            assert order.identifier == custom_ident_gen(order)
        with pytest.raises(ValueError):
            get_order_identifier(order)
