# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.front.template_helpers import general
from shoop.testing.mock_population import populate_if_required
from shoop_tests.front.fixtures import get_jinja_context


@pytest.mark.django_db
def test_get_root_categories():
    populate_if_required()
    context = get_jinja_context()
    for root in general.get_root_categories(context=context):
        assert not root.parent_id


@pytest.mark.django_db
def test_get_newest_products():
    populate_if_required()
    context = get_jinja_context()
    assert len(list(general.get_newest_products(context, n_products=4))) == 4


@pytest.mark.django_db
def test_get_random_products():
    populate_if_required()
    context = get_jinja_context()
    assert len(list(general.get_random_products(context, n_products=4))) == 4


@pytest.mark.django_db
def test_get_all_manufacturers():
    populate_if_required()
    context = get_jinja_context()
    # TODO: This is not a good test
    assert len(general.get_all_manufacturers(context)) == 0
