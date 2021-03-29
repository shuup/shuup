# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import StaffOnlyBehaviorComponent
from shuup.testing.factories import get_default_payment_method, get_default_shop
from shuup_tests.utils.basketish_order_source import BasketishOrderSource
from shuup_tests.utils.fixtures import regular_user

regular_user = regular_user  # noqa


@pytest.mark.django_db
def test_staff_only_behavior(admin_user, regular_user):
    payment_method = get_default_payment_method()
    component = StaffOnlyBehaviorComponent.objects.create()
    payment_method.behavior_components.add(component)
    source = BasketishOrderSource(get_default_shop())

    # anonymous user
    unavailability_reasons = list(payment_method.get_unavailability_reasons(source))
    assert len(unavailability_reasons) == 1

    # regular user
    source.creator = regular_user
    unavailability_reasons = list(payment_method.get_unavailability_reasons(source))
    assert len(unavailability_reasons) == 1

    # admin
    source.creator = admin_user
    unavailability_reasons = list(payment_method.get_unavailability_reasons(source))
    assert len(unavailability_reasons) == 0
