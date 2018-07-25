# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.utils import override_settings

from shuup.admin.modules.contacts import ContactModule
from shuup.admin.modules.contacts.views.detail import ContactDetailView
from shuup.core.models import Contact
from shuup.testing.factories import (
    create_random_person, create_random_user, get_default_shop, get_shop
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import empty_iterable


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


@pytest.mark.django_db
def test_contact_module_search_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        cm = ContactModule()
        contact = create_random_person(locale="en_US", minimum_name_comp_len=5, shop=shop2)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)

        # find the shop
        assert not empty_iterable(cm.get_search_results(request, query=contact.email))
        assert not empty_iterable(cm.get_search_results(request, query=contact.first_name))

        # no shop found
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        assert empty_iterable(cm.get_search_results(request, query=contact.email))
