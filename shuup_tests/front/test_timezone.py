# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.client import Client
from django.urls import reverse

from shuup.core.models import get_person_contact
from shuup.front.views.timezone import SetTimezoneView
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_timezone_view():
    client = Client()
    index_url = reverse("shuup:index")
    tz_url = reverse("shuup:set_timezone")

    response = client.get(index_url)
    assert not response.wsgi_request.session.get("tz")
    assert response.status_code == 200

    response = client.post(tz_url, data={"tz_name": "America/Sao_Paulo"})
    assert response.wsgi_request.session.get("tz") == "America/Sao_Paulo"
    assert response.status_code == 200

    response = client.post(tz_url, data={"tz_name": "America/INVALID"})
    assert response.status_code == 400
    assert response.content.decode("utf-8") == "Invalid timezone"


@pytest.mark.django_db
def test_timezone_middleware(rf, admin_user):
    contact = get_person_contact(admin_user)
    view = SetTimezoneView.as_view()
    assert not contact.timezone

    resp = view(
        apply_request_middleware(rf.post("/", data={"tz_name": "America/Sao_Paulo"}), person=contact, user=admin_user)
    )
    assert resp.status_code == 200

    contact.refresh_from_db()
    assert str(contact.timezone) == "America/Sao_Paulo"
