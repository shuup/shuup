# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import re
import uuid

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from shoop.testing.factories import get_default_shop

username = "u-%d" % uuid.uuid4().time
email = "%s@shoop.local" % username


@pytest.mark.django_db
@pytest.mark.parametrize("requiring_activation", (False, True))
def test_registration(django_user_model, client, requiring_activation):
    if "shoop.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shoop.front.apps.registration required in installed apps")

    get_default_shop()

    with override_settings(
        SHOOP_REGISTRATION_REQUIRES_ACTIVATION=requiring_activation,
    ):
        client.post(reverse("shoop:registration_register"), data={
            "username": username,
            "email": email,
            "password1": "password",
            "password2": "password",
        })
        user = django_user_model.objects.get(username=username)
        if requiring_activation:
            assert not user.is_active
        else:
            assert user.is_active


def test_settings_has_account_activation_days():
    assert hasattr(settings, 'ACCOUNT_ACTIVATION_DAYS')


@pytest.mark.django_db
def test_password_recovery_user_receives_email_1(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shoop.local"
    )
    n_outbox_pre = len(mail.outbox)
    client.post(
        reverse("shoop:recover_password"),
        data={
            "email": user.email
        }
    )
    assert (len(mail.outbox) == n_outbox_pre + 1), "Sending recovery email has failed"
    assert 'http' in mail.outbox[-1].body, "No recovery url in email"
    # ticket #SHOOP-606
    assert 'site_name' not in mail.outbox[-1].body, "site_name variable has no content"


@pytest.mark.django_db
def test_password_recovery_user_receives_email_2(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shoop.local"
    )
    n_outbox_pre = len(mail.outbox)
    # Recover with username
    client.post(
        reverse("shoop:recover_password"),
        data={
            "username": user.username
        }
    )
    assert (len(mail.outbox) == n_outbox_pre + 1), "Sending recovery email has failed"
    assert 'http' in mail.outbox[-1].body, "No recovery url in email"
    assert 'site_name' not in mail.outbox[-1].body, "site_name variable has no content"


@pytest.mark.django_db
def test_password_recovery_user_receives_email_3(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shoop.local"
    )
    get_user_model().objects.create_user(
        username="another_random_person",
        password="asdfg",
        email="random@shoop.local"
    )

    n_outbox_pre = len(mail.outbox)
    # Recover all users with email random@shoop.local
    client.post(
        reverse("shoop:recover_password"),
        data={
            "email": user.email
        }
    )
    assert (len(mail.outbox) == n_outbox_pre + 2), "Sending 2 recovery emails has failed"
    assert 'http' in mail.outbox[-1].body, "No recovery url in email"
    assert 'site_name' not in mail.outbox[-1].body, "site_name variable has no content"


@pytest.mark.django_db
def test_user_will_be_redirected_to_user_account_page_after_activation(client):
    """
    1. Register user
    2. Dig out the urls from the email
    3. Get the url and see where it redirects
    4. See that user's email is in content (in input)
    5. Check that the url poins to user_account-page
    """
    if "shoop.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shoop.front.apps.registration required in installed apps")
    if "shoop.front.apps.customer_information" not in settings.INSTALLED_APPS:
        pytest.skip("shoop.front.apps.customer_information required in installed apps")

    get_default_shop()
    response = client.post(reverse("shoop:registration_register"), data={
        "username": username,
        "email": email,
        "password1": "password",
        "password2": "password",
    }, follow=True)
    body = mail.outbox[-1].body
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', body)
    response = client.get(urls[0], follow=True)
    assert email.encode('utf-8') in response.content, 'email should be found from the page.'
    assert reverse('shoop:customer_edit') == response.request['PATH_INFO'], 'user should be on the account-page.'
