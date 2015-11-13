# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.core import mail
import pytest
from shoop.admin.modules.contacts.views.reset import ContactResetPasswordView
from shoop.testing.factories import get_default_shop, create_random_person
from shoop.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_admin_recovers_clients_password(rf, admin_user):
    get_default_shop()
    person = create_random_person()
    person.user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shoop.local"
    )
    person.save()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    view_func = ContactResetPasswordView.as_view()
    n_outbox_pre = len(mail.outbox)
    view_func(request, pk=person.pk)  # The response doesn't actually matter.
    assert (len(mail.outbox) == n_outbox_pre + 1), "Sending recovery email has failed"
