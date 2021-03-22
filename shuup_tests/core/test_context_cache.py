# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import mock

from shuup.core import cache
from shuup.core.utils import context_cache
from shuup.core.utils.context_cache import _get_items_from_context
from shuup.testing import factories


class Context(object):
    pass


def test_get_items_from_dict_context():
    customer = factories.create_random_person()
    new_customer = factories.create_random_person()
    contact_group = factories.create_random_contact_group()
    contact_group.members.add(customer)

    context = {"customer": customer}
    items = _get_items_from_context(context)
    groups = context_cache._get_val(customer.groups.all())
    assert items["customer_groups"] == groups
    assert "customer" not in items
    # check whether items were cached
    assert cache.get("_ctx_cache:customer_%d" % customer.pk) == groups

    get_val_mock = mock.Mock(wraps=context_cache._get_val)
    with mock.patch.object(context_cache, "_get_val", new=get_val_mock):
        # get items again from the context, it shouldn't invoke _gel_val again for the customer
        get_val_mock.assert_not_called()
        items = _get_items_from_context(context)
        get_val_mock.assert_not_called()

    # check whether cache is bumped after changing contact
    get_val_mock = mock.Mock(wraps=context_cache._get_val)
    with mock.patch.object(context_cache, "_get_val", new=get_val_mock):
        customer.save()
        items = _get_items_from_context(context)
        get_val_mock.assert_called()

    # check whether cache is bumped after changing members of contact group
    get_val_mock = mock.Mock(wraps=context_cache._get_val)
    with mock.patch.object(context_cache, "_get_val", new=get_val_mock):
        items = _get_items_from_context(context)
        get_val_mock.assert_not_called()

        contact_group.members.add(new_customer)

        items = _get_items_from_context(context)
        get_val_mock.assert_called()


def test_get_items_from_obj_context():
    shop = factories.get_default_shop()
    customer = factories.create_random_person()
    contact_group = factories.create_random_contact_group()
    contact_group.members.add(customer)

    context = Context()
    context.customer = customer

    items = _get_items_from_context(context)
    groups = context_cache._get_val(customer.groups.all())

    # check whether items were cached
    assert cache.get("_ctx_cache:customer_%d" % customer.pk) == groups
    assert context._ctx_cache_customer == groups

    assert items["customer_groups"] == groups
    assert "customer" not in items

    get_val_mock = mock.Mock(wraps=context_cache._get_val)
    with mock.patch.object(context_cache, "_get_val", new=get_val_mock):
        # get items again from the context, it shouldn't invoke _gel_val again for the customer
        get_val_mock.assert_not_called()
        items = _get_items_from_context(context)
        get_val_mock.assert_not_called()
        assert items["customer_groups"] == groups
        assert "customer" not in items
