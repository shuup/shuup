# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.http.response import Http404
from django.test.utils import override_settings

from shuup.admin.modules.contacts import ContactModule
from shuup.admin.modules.contacts.views.detail import ContactDetailView
from shuup.admin.modules.contacts.views.list import ContactListView
from shuup.core.models import Contact, get_person_contact
from shuup.testing.factories import (
    create_random_company,
    create_random_person,
    create_random_user,
    get_default_shop,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import empty_iterable


@pytest.mark.django_db
def test_contact_module_search(rf, admin_user):
    shop = get_default_shop()
    cm = ContactModule()
    # This test has a chance to fail if the random person is from a strange locale
    # and the database does not like it. Therefore, use `en_US` here...
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    company = create_random_company(shop)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    assert not empty_iterable(cm.get_search_results(request, query=contact.email))
    assert not empty_iterable(cm.get_search_results(request, query=contact.first_name))
    assert not empty_iterable(cm.get_search_results(request, query=company.name))
    assert empty_iterable(cm.get_search_results(request, query="/"))


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
def test_admin_contact_edit(rf, admin_user):
    shop = get_default_shop()
    admin_contact = get_person_contact(admin_user)

    staff = create_random_user(is_staff=True)
    shop.staff_members.add(staff)
    view_func = ContactDetailView.as_view()

    # non superuser can't edit superuser's contacts
    with pytest.raises(Http404):
        request = apply_request_middleware(rf.get("/"), user=staff)
        response = view_func(request, pk=admin_contact.pk)

    # superuser can
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view_func(request, pk=admin_contact.pk)
    assert response.status_code == 200


@pytest.mark.django_db
def test_contact_module_search_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        cm = ContactModule()
        contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
        contact.add_to_shop(shop2)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)

        # find the shop
        assert not empty_iterable(cm.get_search_results(request, query=contact.email))
        assert not empty_iterable(cm.get_search_results(request, query=contact.first_name))

        # no shop found
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        assert empty_iterable(cm.get_search_results(request, query=contact.email))


@pytest.mark.django_db
def test_contact_list_multiple_shop(rf, admin_user):
    shop1 = get_default_shop()
    shop2 = get_shop(identifier="shop2", name="Shop 2")
    staff = create_random_user(is_staff=True)

    Contact.objects.all().delete()

    shop1.staff_members.add(staff)
    shop2.staff_members.add(staff)

    contact1 = create_random_person(locale="en_US")
    contact1.shops.add(shop1)
    contact2 = create_random_person(locale="en_US")
    contact2.shops.add(shop2)
    contact3 = create_random_company(shop1)
    contact3.shops.add(shop1)
    superuser_contact = get_person_contact(admin_user)

    view_func = ContactListView.as_view()

    # do not send which shop.. it should return all contacts, except superuser contacts
    payload = {"jq": json.dumps({"perPage": 100, "page": 1})}
    request = apply_request_middleware(rf.get("/", data=payload), user=staff)
    response = view_func(request)
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    contacts = [contact["_id"] for contact in data["items"]]
    assert contact1.pk in contacts
    assert contact2.pk in contacts
    assert contact3.pk in contacts
    assert superuser_contact.pk not in contacts

    # request contacts from shop1
    payload = {"jq": json.dumps({"perPage": 100, "page": 1}), "shop": shop1.pk}
    request = apply_request_middleware(rf.get("/", data=payload), user=staff)
    response = view_func(request)
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    contacts = [contact["_id"] for contact in data["items"]]
    assert contact1.pk in contacts
    assert contact2.pk not in contacts
    assert contact3.pk in contacts
    assert superuser_contact.pk not in contacts

    # request contacts from shop2
    payload = {"jq": json.dumps({"perPage": 100, "page": 1}), "shop": shop2.pk}
    request = apply_request_middleware(rf.get("/", data=payload), user=staff)
    response = view_func(request)
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    contacts = [contact["_id"] for contact in data["items"]]
    assert contact1.pk not in contacts
    assert contact2.pk in contacts
    assert contact3.pk not in contacts
    assert superuser_contact.pk not in contacts

    # list all contacts when using a superuser
    payload = {"jq": json.dumps({"perPage": 100, "page": 1})}
    request = apply_request_middleware(rf.get("/", data=payload), user=admin_user)
    response = view_func(request)
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    contacts = [contact["_id"] for contact in data["items"]]
    assert contact1.pk in contacts
    assert contact2.pk in contacts
    assert contact3.pk in contacts
    assert (
        superuser_contact.pk not in contacts
    )  # Superuser must edit the filter values in order to see other superuser contacts.
