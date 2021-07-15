# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.utils import translation

from shuup.admin.modules.orders.views.status import OrderStatusForm
from shuup.core.models import OrderStatus, OrderStatusRole
from shuup.testing.factories import create_default_order_statuses


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "zh-hans"])
def test_default_status(language):
    """Test default order statuses.

    Check can change default statuses
    `name` and `public_name` fields
    but can't change other attributes.
    """
    from django.utils.translation import activate

    activate(language)

    create_default_order_statuses()

    test_new_name = "Test New Name"
    test_new_public_name = "Test New Public Name"
    for status in OrderStatus.objects.all():
        frm = OrderStatusForm(
            languages=[language],
            instance=status,
            default_language=language,
            data={
                "name__{}".format(language): test_new_name,
                "public_name__{}".format(language): test_new_public_name,
                "identifier": "test new identifier",
                "role": OrderStatusRole.NONE,
                "ordering": 100,
                "is_active": not status.is_active,
                "allowed_next_statuses": [o for o in OrderStatus.objects.none()],
            },
        )
        assert frm.is_valid()
        assert not frm.errors
        frm.save(commit=False)
        assert frm.instance.name == test_new_name
        assert frm.instance.public_name == test_new_public_name
        assert frm.instance.identifier == status.identifier
        assert frm.instance.role == status.role
        assert frm.instance.ordering == status.ordering
        assert frm.instance.is_active == status.is_active


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "zh-hans"])
def test_custom_status(language):
    """Test custom order statuses."""
    with translation.override(language):
        create_default_order_statuses()
        status = OrderStatus.objects.create(
            identifier="test-identifier",
            role=OrderStatusRole.INITIAL,
            name="Test Name",
            public_name="Test Public Name",
            ordering=10,
            is_active=False,
            default=False,
        )
    test_new_dentifier = "test-new-identifier"
    test_new_name = "Test New Name"
    test_new_public_name = "Test New Public Name"
    test_new_role = OrderStatusRole.PROCESSING
    test_new_ordering = 100
    test_new_is_active = True
    frm = OrderStatusForm(
        languages=[language],
        instance=status,
        default_language=language,
        data={
            "name__{}".format(language): test_new_name,
            "public_name__{}".format(language): test_new_public_name,
            "identifier": test_new_dentifier,
            "role": test_new_role,
            "ordering": test_new_ordering,
            "is_active": test_new_is_active,
            "allowed_next_statuses": [o for o in OrderStatus.objects.all()],
        },
    )
    assert frm.is_valid()
    assert not frm.errors
    frm.save(commit=False)
    assert frm.instance.name == test_new_name
    assert frm.instance.public_name == test_new_public_name
    assert frm.instance.identifier == test_new_dentifier
    assert frm.instance.role == test_new_role
    assert frm.instance.ordering == test_new_ordering
    assert frm.instance.is_active == test_new_is_active
    assert OrderStatus.objects.get_default_initial() in frm.instance.allowed_next_statuses.all()
    assert OrderStatus.objects.get_default_processing() in frm.instance.allowed_next_statuses.all()
