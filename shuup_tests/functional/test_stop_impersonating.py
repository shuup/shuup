# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user

from shuup.admin.modules.users.views import LoginAsUserView
from shuup.core.models import get_person_contact
from shuup.front.template_helpers.urls import get_logout_url
from shuup.front.views.misc import stop_impersonating
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils.fixtures import regular_user


def is_authenticated(user):
    if callable(getattr(user, "is_authenticated")):  # Django <1.11
        return user.is_authenticated()
    return user.is_authenticated


@pytest.mark.django_db
def test_stop_impersonating(rf, admin_user, regular_user):
    get_default_shop()
    view_func = LoginAsUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    assert get_logout_url({"request": request}) == reverse("shuup:logout")
    get_person_contact(regular_user)
    response = view_func(request, pk=regular_user.pk)
    assert response["location"] == reverse("shuup:index")
    assert get_user(request) == regular_user
    assert "impersonator_user_id" in request.session
    assert get_logout_url({"request": request}) == reverse("shuup:stop-impersonating")
    assert is_authenticated(get_user(request))
    response = stop_impersonating(request)
    assert response.status_code in [301, 302]  # redirect
    assert "impersonator_user_id" not in request.session
    assert is_authenticated(get_user(request))
    assert request.user == admin_user


@pytest.mark.django_db
def test_stop_impersonating_without_impersonating(rf, admin_user, regular_user):
    get_default_shop()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    assert "impersonator_user_id" not in request.session
    response = stop_impersonating(request)
    assert response.status_code == 403
