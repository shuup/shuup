# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model
from django.http.response import Http404
from django.test.utils import override_settings

from shuup.admin.forms.fields import ObjectSelect2MultipleField
from shuup.admin.modules.contacts.forms import CompanyContactBaseForm, PersonContactBaseForm
from shuup.admin.modules.contacts.views import ContactDetailView, ContactEditView, ContactListView
from shuup.core.models import CompanyContact, Gender, PersonContact, get_person_contact
from shuup.testing.factories import (
    create_random_company,
    create_random_person,
    create_random_user,
    get_default_shop,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_person_contact_create_form(rf, admin_user):
    shop = get_default_shop()
    user = get_user_model().objects.create_user(
        username=printable_gibberish(),
        first_name=printable_gibberish(),
        last_name=printable_gibberish(),
    )
    test_first_name = printable_gibberish()
    test_last_name = printable_gibberish()

    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    contact_base_form = PersonContactBaseForm(
        request=request,
        data={"first_name": test_first_name, "last_name": test_last_name, "gender": Gender.UNDISCLOSED.value},
        user=user,
    )

    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.user == user
    assert get_person_contact(user) == contact
    assert contact.name == "%s %s" % (test_first_name, test_last_name)

    assert contact.in_shop(shop)
    assert contact.registered_in(shop)
    assert contact.in_shop(shop, True)


@pytest.mark.django_db
def test_person_contact_edit_form(rf, admin_user):
    shop = get_default_shop()

    # create person without a shop
    person = create_random_person()
    assert not person.in_shop(shop)
    assert not person.registered_in(shop)
    assert not person.in_shop(shop, True)
    new_first_name = "test first name"
    new_name = "%s %s" % (new_first_name, person.last_name)
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    contact_base_form = PersonContactBaseForm(
        request=request,
        instance=person,
        data={"first_name": "test first name", "last_name": person.last_name, "gender": person.gender.value},
    )
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.first_name == new_first_name
    assert contact.name == new_name
    assert person.in_shop(shop)
    assert person.registered_in(shop)
    assert person.in_shop(shop, True)


@pytest.mark.django_db
def test_person_contact_edit_form_2(rf, admin_user):
    shop = get_default_shop()
    person = create_random_person(shop=shop)
    assert person.in_shop(shop)
    assert person.registered_in(shop)
    assert person.in_shop(shop, True)
    new_first_name = "test first name"
    new_name = "%s %s" % (new_first_name, person.last_name)
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    contact_base_form = PersonContactBaseForm(
        request=request,
        instance=person,
        data={"first_name": "test first name", "last_name": person.last_name, "gender": person.gender.value},
    )
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.first_name == new_first_name
    assert contact.name == new_name
    assert person.in_shop(shop)
    assert person.registered_in(shop)
    assert person.in_shop(shop, True)


@pytest.mark.django_db
def test_company_contact_create_form(rf, admin_user):
    shop = get_default_shop()
    company_name = "test company"
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    contact_base_form = CompanyContactBaseForm(
        request=request,
        data={
            "name": company_name,
        },
    )
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert contact.name == company_name
    assert contact.in_shop(shop)
    assert contact.registered_in(shop)
    assert contact.in_shop(shop, True)


@pytest.mark.django_db
def test_company_contact_edit_form(rf, admin_user):
    shop = get_default_shop()
    company = create_random_company()
    assert not company.in_shop(shop)
    assert not company.registered_in(shop)
    assert not company.in_shop(shop, True)
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    new_company_name = "test company"
    contact_base_form = CompanyContactBaseForm(
        request=request,
        instance=company,
        data={
            "name": new_company_name,
        },
    )
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert isinstance(contact_base_form.fields["members"], ObjectSelect2MultipleField)
    assert contact.name == new_company_name
    assert company.in_shop(shop)
    assert company.registered_in(shop)
    assert company.in_shop(shop, True)


@pytest.mark.django_db
def test_company_contact_edit_form_2(rf, admin_user):
    shop = get_default_shop()
    company = create_random_company(shop=shop)
    assert company.in_shop(shop)
    assert company.registered_in(shop)
    assert company.in_shop(shop, True)
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    new_company_name = "test company"
    contact_base_form = CompanyContactBaseForm(
        request=request,
        instance=company,
        data={
            "name": new_company_name,
        },
    )
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert isinstance(contact_base_form.fields["members"], ObjectSelect2MultipleField)
    assert contact.name == new_company_name
    assert company.in_shop(shop)
    assert company.registered_in(shop)
    assert company.in_shop(shop, True)


@pytest.mark.django_db
def test_contact_edit_multishop(rf):
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        staff_user = create_random_user(is_staff=True)

        shop1 = get_shop(identifier="shop-1", enabled=True)
        shop2 = get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        contact = create_random_person(locale="en_US", minimum_name_comp_len=5, shop=shop2)
        # only available in shop2
        assert contact.registered_in(shop2)
        assert contact.in_shop(shop2)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        view = ContactDetailView.as_view()

        # contact not found for this shop
        with pytest.raises(Http404):
            response = view(request, pk=contact.id)

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        response = view(request, pk=contact.id)
        assert response.status_code == 200

        assert contact.registered_in(shop2)
        assert contact.in_shop(shop2)
        assert not contact.registered_in(shop1)
        assert not contact.in_shop(shop1)


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
        with pytest.raises(Http404):
            response = view(request, pk=contact.id)
        # permission granted for contact and shop2
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        response = view(request, pk=contact.id)
        assert response.status_code == 200

        # permission denied for company and shop2
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        with pytest.raises(Http404):
            response = view(request, pk=company.id)
        # permission granted for company and shop1
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        response = view(request, pk=company.id)
        assert response.status_code == 200

        # contact belongs to shop 1
        assert not contact.registered_in(shop1)
        assert not contact.in_shop(shop1)
        assert contact.registered_in(shop2)
        assert contact.in_shop(shop2)

        # company belongs to shop 2
        assert not company.registered_in(shop2)
        assert not company.in_shop(shop2)
        assert company.registered_in(shop1)
        assert company.in_shop(shop1)

        # save contact under shop 1
        request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop1)
        contact_base_form = PersonContactBaseForm(
            request=request,
            instance=contact,
            data={"first_name": "test first name", "last_name": contact.last_name, "gender": contact.gender.value},
        )
        assert contact_base_form.is_valid(), contact_base_form.errors
        contact_base_form.save()
        contact.refresh_from_db()

        assert contact.registered_in(shop2)
        assert not contact.registered_in(shop1)
        assert contact.in_shop(shop1)
        assert contact.in_shop(shop2)

        # save company under shop 2
        request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop2)
        form = CompanyContactBaseForm(
            request=request,
            instance=company,
            data={
                "name": "eww",
            },
        )
        assert form.is_valid(), form.errors
        form.save()
        company.refresh_from_db()

        assert company.registered_in(shop1)
        assert not company.registered_in(shop2)
        assert company.in_shop(shop1)
        assert company.in_shop(shop2)


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
        with pytest.raises(Http404):
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

        company = create_random_company()
        # only available in shop1
        company.add_to_shop(shop1)

        view = ContactDetailView.as_view()

        # company not found for this shop
        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        with pytest.raises(Http404):
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
        company = create_random_company()
        company.add_to_shop(shop1)

        view = ContactListView()

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop1)
        view.request = request
        assert company in view.get_queryset()
        assert contact not in view.get_queryset()

        request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop2)
        view.request = request
        assert contact in view.get_queryset()
        assert company not in view.get_queryset()
