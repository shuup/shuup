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

from shoop.testing.factories import get_default_shop
from shoop.testing.soup_utils import extract_form_fields
from shoop_tests.utils import SmartClient


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
    assert soup.find(attrs={"name": "contact-name"})["value"] == user.get_full_name()

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
    response = SmartClient().get(reverse("shoop:customer_edit"), follow=False)
    assert response.status_code == 302  # Redirection ("Found")
    assert resolve_url(settings.LOGIN_URL) in response.url
