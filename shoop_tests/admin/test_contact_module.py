# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.admin.modules.contacts import ContactModule
from shoop.admin.modules.contacts.views.detail import ContactDetailView
from shoop.core.models import Contact
from shoop.testing.factories import create_random_person, get_default_shop
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils import empty_iterable


@pytest.mark.django_db
def test_contact_module_search(rf):
    cm = ContactModule()
    # This test has a chance to fail if the random person is from a strange locale
    # and the database does not like it. Therefore, use `en_US` here...
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = rf.get("/")
    assert not empty_iterable(cm.get_search_results(request, query=contact.email))
    assert not empty_iterable(cm.get_search_results(request, query=contact.first_name))
    assert empty_iterable(cm.get_search_results(request, query=contact.email[0]))


@pytest.mark.django_db
def test_contact_set_is_active(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    assert contact.is_active

    request = apply_request_middleware(rf.post("/", {"set_is_active": "0"}), user=admin_user)
    view_func = ContactDetailView.as_view()
    response = view_func(request, pk=contact.pk)
    assert response.status_code < 500 and not Contact.objects.get(pk=contact.pk).is_active

    request = apply_request_middleware(rf.post("/", {"set_is_active": "1"}), user=admin_user)
    view_func = ContactDetailView.as_view()
    response = view_func(request, pk=contact.pk)
    assert response.status_code < 500 and Contact.objects.get(pk=contact.pk).is_active
