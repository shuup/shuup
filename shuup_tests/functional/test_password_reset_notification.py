# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core import mail
from django.utils.translation import activate

from shuup.notify.script_templates import PasswordResetTemplate
from shuup.testing.factories import get_default_shop
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
@pytest.mark.parametrize("request_recovery_view_url_name", ("shuup:recover_password", "shuup_admin:request_password"))
def test_password_reset_script_with_password_reset_form(client, admin_user, request_recovery_view_url_name):
    activate("en")

    shop = get_default_shop()
    script_template = PasswordResetTemplate()
    form = script_template.get_form()
    initial = script_template.get_initial()
    for k, v in form.initial.items():
        assert initial[k] == v

    data = {
        "base-send_to": "customer",
        "en-body": "this should be something unique the default template will not be -{{ recovery_url }}",
        "en-subject": "some subject",
    }
    form = script_template.get_form(data=data)
    assert form.is_valid()
    script = script_template.create_script(shop, form)

    assert script.event_identifier == PasswordResetTemplate.identifier
    assert script.enabled

    n_outbox_pre = len(mail.outbox)
    client.post(reverse(request_recovery_view_url_name), data={"email": admin_user.email})
    assert len(mail.outbox) == n_outbox_pre + 1
    assert "something unique the default template" in mail.outbox[-1].body

    recovery_url = mail.outbox[-1].body.split("-")[1]
    response = client.get(recovery_url)
    assert response.status_code == 301
