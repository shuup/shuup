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


@pytest.mark.django_db
@pytest.mark.parametrize("allow_image_uploads", (False, True))
def test_uploads_allowed_setting(client, allow_image_uploads, regular_user):
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    with override_settings(SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD=allow_image_uploads):
        if allow_image_uploads:
            tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
            generate_image(120, 120).save(tmp_file)
            with open(tmp_file.name, "rb") as data:
                response = client.post(reverse("shuup:media-upload"), data=dict({"file": data}), format="multipart")
            assert response.status_code == 200
            data = json.loads(response.content.decode("utf-8"))
            assert data["file"]["id"]
        else:
            tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
            generate_image(120, 120).save(tmp_file)
            with open(tmp_file.name, "rb") as data:
                response = client.post(reverse("shuup:media-upload"), data=dict({"file": data}), format="multipart")
            assert response.status_code == 403


@pytest.mark.django_db
def test_anon_uploads(client):
    with override_settings(SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD=True):
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        generate_image(120, 120).save(tmp_file)
        with open(tmp_file.name, "rb") as data:
            response = client.post(reverse("shuup:media-upload"), data=dict({"file": data}), format="multipart")
        assert response.status_code == 302  # Anon uploads not allowed


@pytest.mark.django_db
def test_with_invalid_image(client, regular_user):
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    with override_settings(SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD=True):
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        tmp_file.write(b"Hello world!")
        tmp_file.seek(0)
        with open(tmp_file.name, "rb") as data:
            response = client.post(reverse("shuup:media-upload"), data=dict({"file": data}), format="multipart")
        assert response.status_code == 400
        data = json.loads(response.content.decode("utf-8"))
        assert "not an image or a corrupted image" in data["error"]


@pytest.mark.django_db
def test_large_file(client, regular_user):
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    with override_settings(SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD=True):
        with override_settings(SHUUP_FRONT_MAX_UPLOAD_SIZE=10):
            tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
            generate_image(120, 120).save(tmp_file)
            with open(tmp_file.name, "rb") as data:
                response = client.post(reverse("shuup:media-upload"), data=dict({"file": data}), format="multipart")
            assert response.status_code == 400
            data = json.loads(response.content.decode("utf-8"))
            assert "Maximum file size reached" in data["error"]
