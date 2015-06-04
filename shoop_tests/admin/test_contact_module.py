# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.admin.modules.contacts import ContactModule
from shoop.testing.factories import create_random_person
from shoop_tests.utils import empty_iterable


@pytest.mark.django_db
def test_contact_module_search(rf):
    cm = ContactModule()
    # This test has a chance to fail if the random person is from a strange locale
    # and the database does not like it. Therefore, use `en_US` here...
    contact = create_random_person(locale="en_US")
    request = rf.get("/")
    assert not empty_iterable(cm.get_search_results(request, query=contact.email))
    assert not empty_iterable(cm.get_search_results(request, query=contact.first_name))
    assert empty_iterable(cm.get_search_results(request, query=contact.email[0]))
