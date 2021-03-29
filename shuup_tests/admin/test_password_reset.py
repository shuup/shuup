# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core import mail
from django.utils.html import escape

from shuup.testing import factories
from shuup.testing.factories import get_default_shop
from shuup.utils.django_compat import reverse
from shuup_tests.utils.fixtures import REGULAR_USER_EMAIL, REGULAR_USER_PASSWORD


@pytest.mark.django_db
def test_reset_admin_user_password(client):
    get_default_shop()

    user = factories.create_random_user("en", is_staff=True, is_active=True, email=REGULAR_USER_EMAIL)
    user.set_password(REGULAR_USER_PASSWORD)
    user.save(update_fields=("password",))

    assert len(mail.outbox) == 0
    response = client.post(reverse("shuup_admin:request_password"), data={"email": user.email})
    assert response.status_code == 302
    assert response.get("location")
    assert response.get("location").endswith(reverse("shuup_admin:login"))
    assert len(mail.outbox) == 1
    email_content = mail.outbox[0].body
    url = email_content[email_content.find("http") :]
    _, _, _, _, _, uid, token, _ = url.split("/")

    new_password = "new_pass"
    response = client.post(
        reverse("shuup_admin:recover_password", kwargs=dict(uidb64=uid, token=token)),
        data={"new_password1": new_password, "new_password2": new_password},
    )
    assert response.status_code == 302
    assert response.get("location")
    assert response.get("location").endswith(reverse("shuup_admin:dashboard"))
    assert len(mail.outbox) == 1

    user.refresh_from_db()
    assert user.check_password(new_password)


@pytest.mark.django_db
def test_reset_admin_user_password_errors(client):
    get_default_shop()

    user = factories.create_random_user("en", is_staff=True, is_active=False, email=REGULAR_USER_EMAIL)
    user.set_password(REGULAR_USER_PASSWORD)
    user.save()

    assert len(mail.outbox) == 0

    # user not active
    response = client.post(reverse("shuup_admin:request_password"), data={"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 0

    user.is_active = True
    user.is_staff = False
    user.save()

    # user not staff
    response = client.post(reverse("shuup_admin:request_password"), data={"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 0

    # non-existent email
    response = client.post(reverse("shuup_admin:request_password"), data={"email": "doesntexist@email.ok"})
    assert response.status_code == 302
    assert len(mail.outbox) == 0

    user.is_staff = True
    user.save()

    # all set
    response = client.post(reverse("shuup_admin:request_password"), data={"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    email_content = mail.outbox[0].body
    url = email_content[email_content.find("http") :]
    _, _, _, _, _, uid, token, _ = url.split("/")

    # invalid token
    new_password = "new_pass"
    response = client.post(
        reverse("shuup_admin:recover_password", kwargs=dict(uidb64=uid, token="invalid")),
        data={"new_password1": new_password, "new_password2": new_password},
    )
    assert response.status_code == 400
    assert "This recovery link is invalid" in response.content.decode("utf-8")

    # invalid uid
    response = client.post(
        reverse("shuup_admin:recover_password", kwargs=dict(uidb64="uid", token=token)),
        data={"new_password1": new_password, "new_password2": new_password},
    )
    assert response.status_code == 400
    assert "This recovery link is invalid" in response.content.decode("utf-8")

    # invalid passwords
    response = client.post(
        reverse("shuup_admin:recover_password", kwargs=dict(uidb64=uid, token=token)),
        data={"new_password1": new_password, "new_password2": "wrong"},
    )
    assert response.status_code == 200  # Django forms likes to return invalid forms as 200. So be it.
    assert escape("The two password fields didn't match.") in response.content.decode("utf-8")

    # all good
    response = client.post(
        reverse("shuup_admin:recover_password", kwargs=dict(uidb64=uid, token=token)),
        data={"new_password1": new_password, "new_password2": new_password},
    )
    assert response.status_code == 302
