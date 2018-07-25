# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test.utils import override_settings

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.modules.contacts.forms import (
    CompanyContactBaseForm, PersonContactBaseForm
)
from shuup.admin.modules.contacts.views import (
    ContactDetailView, ContactEditView, ContactListView
)
from shuup.admin.shop_provider import SHOP_SESSION_KEY
from shuup.core.models import (
    CompanyContact, Gender, get_person_contact, PersonContact
)
from shuup.testing.factories import (
    create_random_company, create_random_person, create_random_user, get_shop
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_person_contact_create_form(rf, admin_user):
    user = get_user_model().objects.create_user(
        username=printable_gibberish(),
        first_name=printable_gibberish(),
        last_name=printable_gibberish(),
    )
    test_first_name = printable_gibberish()
    test_last_name = printable_gibberish()

    request = apply_request_middleware(rf.post("/"), user=admin_user)
    contact_base_form = PersonContactBaseForm(request=request, data={
        "first_name": test_first_name,
        "last_name": test_last_name,
        "gender": Gender.UNDISCLOSED.value
    }, user=user)

    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.user == user
    assert get_person_contact(user) == contact
    assert contact.name == "%s %s" % (test_first_name, test_last_name)


@pytest.mark.django_db
def test_person_contact_edit_form(rf, admin_user):
    person = create_random_person()
    new_first_name = "test first name"
    new_name = "%s %s" % (new_first_name, person.last_name)
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    contact_base_form = PersonContactBaseForm(request=request, instance=person, data={
        "first_name": "test first name",
        "last_name": person.last_name,
        "gender": person.gender.value
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.first_name == new_first_name
    assert contact.name == new_name


@pytest.mark.django_db
def test_company_contact_create_form(rf, admin_user):
    company_name = "test company"
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    contact_base_form = CompanyContactBaseForm(request=request, data={
        "name": company_name,
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert contact.name == company_name


@pytest.mark.django_db
def test_company_contact_edit_form(rf, admin_user):
    company = create_random_company()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    new_company_name = "test company"
    contact_base_form = CompanyContactBaseForm(request=request, instance=company, data={
        "name": new_company_name,
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert isinstance(contact_base_form.fields["members"], Select2MultipleField)
    assert contact.name == new_company_name


@pytest.mark.django_db
def test_contact_edit_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        # only available in shop2
        contact = create_random_person(locale="en_US", minimum_name_comp_len=5, shop=shop2)
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        view = ContactDetailView.as_view()

        # contact not found for this shop
        with pytest.raises(PermissionDenied):
            response = view(request, pk=contact.id)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        response = view(request, pk=contact.id)
        assert response.status_code == 200


@pytest.mark.django_db
def test_contact_company_edit_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        # only available in shop2
        contact = create_random_person(locale="en_US", minimum_name_comp_len=5, shop=shop2)

        # only available in shop1
        company = create_random_company(shop1)

        view = ContactEditView.as_view()

        # permission denied for contact and shop1
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        with pytest.raises(PermissionDenied):
            response = view(request, pk=contact.id)
        # permission granted for contact and shop2
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        response = view(request, pk=contact.id)
        assert response.status_code == 200

        # permission denied for company and shop2
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        with pytest.raises(PermissionDenied):
            response = view(request, pk=company.id)
        # permission granted for company and shop1
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        response = view(request, pk=company.id)
        assert response.status_code == 200


@pytest.mark.django_db
def test_contact_detail_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        contact = create_random_person(locale="en_US", minimum_name_comp_len=5, shop=shop2)

        view = ContactDetailView.as_view()

        # contact not found for this shop
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        with pytest.raises(PermissionDenied):
            response = view(request, pk=contact.id)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        response = view(request, pk=contact.id)
        assert response.status_code == 200


@pytest.mark.django_db
def test_company_contact_detail_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        company = create_random_company(shop1)
        assert company.groups.count() == 1

        view = ContactDetailView.as_view()

        # company not found for this shop
        assert company.groups.filter(shop=shop1).exists()
        assert not company.groups.filter(shop=shop2).exists()
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        assert company.groups.filter(shop=shop1).exists()
        assert not company.groups.filter(shop=shop2).exists()
        with pytest.raises(PermissionDenied):
            response = view(request, pk=company.id)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        response = view(request, pk=company.id)
        assert response.status_code == 200


@pytest.mark.django_db
def test_contact_company_list_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        # only available in shop2
        contact = create_random_person(locale="en_US", minimum_name_comp_len=5, shop=shop2)

        # only available in shop1
        company = create_random_company(shop1)

        view = ContactListView()

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        view.request = request
        assert company in view.get_queryset()
        assert contact not in view.get_queryset()

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        view.request = request
        assert contact in view.get_queryset()
        assert company not in view.get_queryset()
