# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import django.core.mail as mail
import pytest
from django.conf import settings

from shuup.notify import Context
from shuup.notify.actions.email import SendEmail
from shuup_tests.notify.fixtures import (
    get_initialized_test_event, TEST_TEMPLATE_DATA
)
from shuup_tests.utils import prepare_logger_for_stdout, printable_gibberish


@pytest.mark.django_db
def test_email_action():
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
        pytest.skip("Need locmem email backend")

    mail.outbox = []  # Clear the Django testing mail outbox

    event = get_initialized_test_event()
    ctx = Context.from_event(event)
    ctx.set("name", "Luke Warm")  # This variable isn't published by the event, but it's used by the template
    se = SendEmail({
        "template_data": TEST_TEMPLATE_DATA,
        "recipient": {"constant": "someone@shuup.local"},
        "language": {"constant": "ja"},
        "send_identifier": {"constant": "hello, hello, hello"}
    })
    se.execute(ctx)  # Once,
    se.execute(ctx)  # Twice!
    assert len(mail.outbox) == 1  # 'send_identifier' should ensure this is true
    msg = mail.outbox[0]
    assert msg.to == ['someone@shuup.local']
    assert ctx.get("name").upper() in msg.subject  # The Japanese template upper-cases the name
