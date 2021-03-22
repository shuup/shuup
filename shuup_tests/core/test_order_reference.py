# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import hashlib
import pytest
from django.test import override_settings

from shuup import configuration
from shuup.core.models import ConfigurationItem
from shuup.core.models._order_utils import get_order_identifier, get_reference_number
from shuup.testing.factories import create_empty_order, get_default_shop


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
    methods = (custom_refno_gen, "%s.%s" % (__name__, custom_refno_gen.__name__))
    for method in methods:
        with override_settings(SHUUP_REFERENCE_NUMBER_METHOD=method):
            order = create_empty_order()
            order.save()
            assert order.reference_number == custom_refno_gen(order)
        with pytest.raises(ValueError):
            get_reference_number(order)


@pytest.mark.django_db
def test_custom_ident_generation():
    methods = (custom_ident_gen, "%s.%s" % (__name__, custom_ident_gen.__name__))
    for method in methods:
        with override_settings(SHUUP_ORDER_IDENTIFIER_METHOD=method):
            order = create_empty_order()
            order.save()
            assert order.identifier == custom_ident_gen(order)
        with pytest.raises(ValueError):
            get_order_identifier(order)


@pytest.mark.django_db
def test_ref_lengths():
    from shuup.admin.modules.settings import consts
    from shuup.admin.modules.settings.enums import OrderReferenceNumberMethod

    # clear shop configurations
    shop = get_default_shop()

    ConfigurationItem.objects.filter(shop=shop).delete()
    order = create_empty_order(shop=shop)
    order.save()
    order.reference_number = None
    order.save()

    ref_number = get_reference_number(order)  # by default we return "unique"
    assert len(ref_number) == 17 + 1  # unique ref + checksum

    order.reference_number = None
    order.save()

    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD, OrderReferenceNumberMethod.UNIQUE.value)
    ref_number = get_reference_number(order)
    assert len(ref_number) == 17 + 1  # unique ref + checksum

    order.reference_number = None
    order.save()

    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD, 25)
    ref_number = get_reference_number(order)
    assert len(ref_number) == 25 + 1  # unique ref + checksum

    order.reference_number = None
    order.save()

    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD, 19)
    ref_number = get_reference_number(order)
    assert len(ref_number) == 19 + 1  # Finnish case

    order.reference_number = None
    order.save()

    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD, OrderReferenceNumberMethod.RUNNING.value)
    ref_number = get_reference_number(order)
    assert len(ref_number) == 19 + 1
    order.reference_number = None
    order.save()

    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD, "123")
    ref_number = get_reference_number(order)
    assert len(ref_number) == 19 + 1
    order.reference_number = None
    order.save()

    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD, 123)
    ref_number = get_reference_number(order)
    assert len(ref_number) == 19 + 1  # Finnish case
    order.reference_number = None
    order.save()

    # reset prefix
    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD, "")
    configuration.set(shop, consts.ORDER_REFERENCE_NUMBER_METHOD_FIELD, OrderReferenceNumberMethod.SHOP_RUNNING.value)
    ref_number = get_reference_number(order)
    assert len(ref_number) == 19 + 1  # Finnish case
    order.reference_number = None
    order.save()
