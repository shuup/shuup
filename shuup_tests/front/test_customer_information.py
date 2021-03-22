# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import pytest
import tempfile
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.shortcuts import resolve_url
from django.test import override_settings

from shuup import configuration
from shuup.core.models import CompanyContact, get_company_contact, get_person_contact
from shuup.core.utils.users import force_anonymous_contact_for_user
from shuup.front.apps.customer_information.forms import PersonContactForm
from shuup.front.views.dashboard import DashboardView
from shuup.testing.factories import create_random_user, generate_image, get_default_shop
from shuup.testing.soup_utils import extract_form_fields
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient
from shuup_tests.utils.fixtures import REGULAR_USER_PASSWORD, REGULAR_USER_USERNAME, regular_user

User = get_user_model()


def default_customer_data():
    return {
        "contact-first_name": "Captain",
        "contact-last_name": "Shuup",
        "contact-email": "captain@shuup.local",
        "contact-gender": "o",
    }


def default_company_data():
    return {
        "contact-name": "Fakerr",
        "contact-tax_number": "111110",
        "contact-phone": "11-111-111-1110",
        "contact-email": "captain@shuup.local",
    }


def default_address_data(address_type):
    return {
        "{}-name".format(address_type): "Fakerr",
        "{}-phone".format(address_type): "11-111-111-1110",
        "{}-email".format(address_type): "captain@shuup.local",
        "{}-street".format(address_type): "123 Fake St.",
        "{}-postal_code".format(address_type): "1234567",
        "{}-city".format(address_type): "Shuupville",
        "{}-country".format(address_type): "US",
    }


@pytest.mark.django_db
@pytest.mark.parametrize("allow_image_uploads", (False, True))
def test_new_user_information_edit(allow_image_uploads):
    with override_settings(SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD=allow_image_uploads):
        client = SmartClient()
        get_default_shop()
        # create new user
        user_password = "niilo"
        user = get_user_model().objects.create_user(
            username="Niilo_Nyyppa",
            email="niilo@example.shuup.com",
            password=user_password,
            first_name="Niilo",
            last_name="Nyyppä",
        )

        client.login(username=user.username, password=user_password)

        # make sure all information matches in form
        customer_edit_url = reverse("shuup:customer_edit")
        soup = client.soup(customer_edit_url)

        assert soup.find(attrs={"name": "contact-email"})["value"] == user.email
        assert soup.find(attrs={"name": "contact-first_name"})["value"] == user.first_name
        assert soup.find(attrs={"name": "contact-last_name"})["value"] == user.last_name

        # Test POSTing
        form = extract_form_fields(soup)
        new_email = "nyyppa@example.shuup.com"
        form["contact-email"] = new_email
        form["contact-country"] = "FI"

        for prefix in ("billing", "shipping"):
            form["%s-name" % prefix] = user.first_name
            form["%s-city" % prefix] = "test-city"
            form["%s-email" % prefix] = new_email
            form["%s-street" % prefix] = "test-street"
            form["%s-country" % prefix] = "FI"

        if allow_image_uploads:
            tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
            generate_image(120, 120).save(tmp_file)
            with open(tmp_file.name, "rb") as data:
                response = client.post(reverse("shuup:media-upload"), data=dict({"file": data}), format="multipart")
            assert response.status_code == 200
            data = json.loads(response.content.decode("utf-8"))
            file_id = data["file"]["id"]
            form["contact-picture"] = file_id

        response, soup = client.response_and_soup(customer_edit_url, form, "post")
        assert response.status_code == 302
        user = get_user_model().objects.get(pk=user.pk)
        assert user.email == new_email
        contact = get_person_contact(user)

        if allow_image_uploads:
            assert contact.picture.id == file_id

            # Fetch page and check that the picture rendered there
            customer_edit_url = reverse("shuup:customer_edit")
            soup = client.soup(customer_edit_url)
            assert int(soup.find(attrs={"id": "id_contact-picture-dropzone"})["data-id"]) == file_id
        else:
            assert contact.picture is None


@pytest.mark.django_db
def test_customer_edit_redirects_to_login_if_not_logged_in():
    get_default_shop()  # Front middleware needs a Shop to exists
    urls = ["shuup:customer_edit", "shuup:company_edit"]
    for url in urls:
        response = SmartClient().get(reverse(url), follow=False)
        assert response.status_code == 302  # Redirection ("Found")
        assert resolve_url(settings.LOGIN_URL) in response.url


@pytest.mark.django_db
@pytest.mark.parametrize("allow_company_registration", (False, True))
def test_company_edit_form_links_company(regular_user, allow_company_registration):
    get_default_shop()
    configuration.set(None, "allow_company_registration", allow_company_registration)
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)

    data = default_company_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))
    company_edit_url = reverse("shuup:company_edit")

    if allow_company_registration:
        soup = client.soup(company_edit_url)
        response, soup = client.response_and_soup(company_edit_url, data, "post")
        assert response.status_code == 302
        assert get_company_contact(regular_user)
    else:
        response = client.get(company_edit_url)
        assert reverse("shuup:customer_edit") in response.url
        response = client.post(company_edit_url, data)
        assert reverse("shuup:customer_edit") in response.url


@pytest.mark.django_db
def test_company_still_linked_if_customer_contact_edited(regular_user):
    get_default_shop()
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    company = CompanyContact()
    company.save()
    company.members.add(person)
    assert get_company_contact(regular_user)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    customer_edit_url = reverse("shuup:customer_edit")
    soup = client.soup(customer_edit_url)

    data = default_customer_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(customer_edit_url, data, "post")

    assert response.status_code == 302
    assert get_company_contact(regular_user)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password_value,new_password_2,expected",
    [
        (REGULAR_USER_PASSWORD, "12345", True),
        ("some_other_password", "12345", False),
        (REGULAR_USER_PASSWORD, "12345678", False),
    ],
)
def test_user_change_password(regular_user, password_value, new_password_2, expected):
    get_default_shop()
    assert check_password(REGULAR_USER_PASSWORD, regular_user.password)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    change_password_url = reverse("shuup:change_password")

    new_password = "12345"
    data = {
        "old_password": password_value,
        "new_password1": new_password,
        "new_password2": new_password_2,
    }

    response, soup = client.response_and_soup(change_password_url, data, "post")
    user = get_user_model().objects.get(pk=regular_user.pk)
    assert regular_user == user

    assert check_password(REGULAR_USER_PASSWORD, user.password) != expected
    assert check_password(new_password, user.password) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("allow_company_registration", (False, True))
def test_company_tax_number_limitations(regular_user, allow_company_registration):
    get_default_shop()
    configuration.set(None, "allow_company_registration", allow_company_registration)
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    if allow_company_registration:
        client = SmartClient()
        client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
        company_edit_url = reverse("shuup:company_edit")
        soup = client.soup(company_edit_url)

        data = default_company_data()
        data.update(default_address_data("billing"))
        data.update(default_address_data("shipping"))

        response, soup = client.response_and_soup(company_edit_url, data, "post")

        assert response.status_code == 302
        assert get_company_contact(regular_user)

        # re-save should work properly
        response, soup = client.response_and_soup(company_edit_url, data, "post")
        assert response.status_code == 302
        client.logout()

        # another company tries to use same tax number
        new_user_password = "derpy"
        new_user_username = "derpy"
        user = User.objects.create_user(new_user_username, "derpy@shuup.com", new_user_password)
        person = get_person_contact(user=user)
        assert not get_company_contact(user)

        client = SmartClient()
        client.login(username=new_user_username, password=new_user_password)
        company_edit_url = reverse("shuup:company_edit")
        soup = client.soup(company_edit_url)

        data = default_company_data()
        data.update(default_address_data("billing"))
        data.update(default_address_data("shipping"))

        response, soup = client.response_and_soup(company_edit_url, data, "post")
        assert response.status_code == 200  # this time around, nothing was saved.
        assert not get_company_contact(user)  # company contact yet

        # change tax number
        data["contact-tax_number"] = "111111"
        response, soup = client.response_and_soup(company_edit_url, data, "post")
        assert response.status_code == 302  # this time around, nothing was saved.
        assert get_company_contact(user)  # company contact yet

        # go back to normal and try to get tax number approved
        data["contact-tax_number"] = "111110"
        response, soup = client.response_and_soup(company_edit_url, data, "post")
        assert response.status_code == 200  # this time around, nothing was saved.
    else:
        client = SmartClient()
        client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
        company_edit_url = reverse("shuup:company_edit")
        response = client.get(company_edit_url)
        assert reverse("shuup:customer_edit") in response.url


@pytest.mark.django_db
def test_person_contact_form_field_overrides():
    with override_settings(SHUUP_PERSON_CONTACT_FIELD_PROPERTIES={}):
        form = PersonContactForm()
        assert type(form.fields["gender"].widget) != forms.HiddenInput
        assert form.fields["phone"].required is False

    with override_settings(
        SHUUP_PERSON_CONTACT_FIELD_PROPERTIES={"gender": {"widget": forms.HiddenInput()}, "phone": {"required": True}}
    ):
        form = PersonContactForm()
        assert type(form.fields["gender"].widget) == forms.HiddenInput
        assert form.fields["phone"].required is True


@pytest.mark.django_db
def test_dashboard_invisible_for_guests(rf):
    user = create_random_user()
    request = apply_request_middleware(rf.get("/"), user=user)
    view = DashboardView.as_view()

    # all ok
    response = view(request)
    assert response.status_code == 200

    force_anonymous_contact_for_user(user)
    request = apply_request_middleware(rf.get("/"), user=user)
    response = view(request)
    assert response.status_code == 302
