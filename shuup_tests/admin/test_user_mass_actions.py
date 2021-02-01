# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest
from shuup.admin.modules.users.mass_actions import ResetPasswordAction
from shuup.admin.modules.users.views import UserListView
from shuup.core.models import Order, OrderStatusRole
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_shop, get_default_supplier, create_random_user
)
from shuup.testing.utils import apply_request_middleware
from django.core import mail
from shuup.core.utils import users as users_module


@pytest.mark.django_db
def test_user_reset_pwd_mass_aation(rf, admin_user):
    shop = get_default_shop()
    user = create_random_user(email="user@user.com")
    staff = create_random_user(is_staff=True, email="staff@staff.com")

    payload = {
        "action": ResetPasswordAction().identifier,
        "values": "all"
    }
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    view = UserListView.as_view()

    assert len(mail.outbox) == 0
    response = view(request=request)
    assert response.status_code == 200
    # sent three emails, one for each user
    assert len(mail.outbox) == 3

    payload = {
        "action": ResetPasswordAction().identifier,
        "values": [user.pk, staff.pk]
    }
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    response = view(request=request)
    assert response.status_code == 200
    assert len(mail.outbox) == 5
