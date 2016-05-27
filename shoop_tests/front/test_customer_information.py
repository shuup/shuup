# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.shortcuts import resolve_url

from shoop.core.models import (
    CompanyContact, get_company_contact, get_person_contact
)
from shoop.front.apps.customer_information.views import (
    CompanyEditView, CustomerEditView
)
from shoop.testing.factories import get_default_shop
from shoop.testing.soup_utils import extract_form_fields
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils import SmartClient
from shoop_tests.utils.fixtures import (
    regular_user, REGULAR_USER_PASSWORD, REGULAR_USER_USERNAME
)


def default_customer_data():
    return {
        "contact-first_name": "Captain",
        "contact-last_name": "Shoop",
        "contact-email": "captain@shoop.local",
        "contact-gender": "o",
    }


def default_company_data():
    return {
        "contact-name": "Fakerr",
        "contact-tax_number": "111110",
        "contact-phone": "11-111-111-1110",
        "contact-email": "captain@shoop.local",
    }


def default_address_data(address_type):
    return {
        "{}-name".format(address_type) : "Fakerr",
        "{}-phone".format(address_type): "11-111-111-1110",
        "{}-email".format(address_type): "captain@shoop.local",
        "{}-street".format(address_type): "123 Fake St.",
        "{}-postal_code".format(address_type): "1234567",
        "{}-city".format(address_type): "Shoopville",
        "{}-country".format(address_type): "US",
    }


@pytest.mark.django_db
def test_new_user_information_edit():
    client = SmartClient()
    get_default_shop()
    # create new user
    user_password = "niilo"
    user = get_user_model().objects.create_user(
        username="Niilo_Nyyppa",
        email="niilo@example.shoop.io",
        password=user_password,
        first_name="Niilo",
        last_name="Nyyppä",
    )

    client.login(username=user.username, password=user_password)

    # make sure all information matches in form
    customer_edit_url = reverse("shoop:customer_edit")
    soup = client.soup(customer_edit_url)

    assert soup.find(attrs={"name": "contact-email"})["value"] == user.email
    assert soup.find(attrs={"name": "contact-first_name"})["value"] == user.first_name
    assert soup.find(attrs={"name": "contact-last_name"})["value"] == user.last_name

    # Test POSTing
    form = extract_form_fields(soup)
    new_email = "nyyppa@example.shoop.io"
    form["contact-email"] = new_email
    form["contact-country"] = "FI"

    for prefix in ("billing", "shipping"):
        form["%s-city" % prefix] = "test-city"
        form["%s-email" % prefix] = new_email
        form["%s-street" % prefix] = "test-street"
        form["%s-country" % prefix] = "FI"

    response, soup = client.response_and_soup(customer_edit_url, form, "post")

    assert response.status_code == 302
    assert get_user_model().objects.get(pk=user.pk).email == new_email


@pytest.mark.django_db
def test_customer_edit_redirects_to_login_if_not_logged_in():
    get_default_shop()  # Front middleware needs a Shop to exists
    urls = ["shoop:customer_edit", "shoop:company_edit"]
    for url in urls:
        response = SmartClient().get(reverse(url), follow=False)
        assert response.status_code == 302  # Redirection ("Found")
        assert resolve_url(settings.LOGIN_URL) in response.url


@pytest.mark.django_db
def test_company_edit_form_links_company(regular_user, rf):
    get_default_shop()
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    company_edit_url = reverse("shoop:company_edit")
    soup = client.soup(company_edit_url)

    data = default_company_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(company_edit_url, data, "post")

    assert response.status_code == 302
    assert get_company_contact(regular_user)


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
    customer_edit_url = reverse("shoop:customer_edit")
    soup = client.soup(customer_edit_url)

    data = default_customer_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(customer_edit_url, data, "post")

    assert response.status_code == 302
    assert get_company_contact(regular_user)
