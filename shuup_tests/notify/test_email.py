# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django.core.mail as mail
import mock
import pytest
from django.conf import settings
from django.test import override_settings

from shuup.notify.actions.email import SendEmail
from shuup.notify.models import EmailTemplate
from shuup.notify.script import Context
from shuup.notify.signals import notification_email_before_send, notification_email_sent
from shuup.testing import factories
from shuup_tests.notify.fixtures import TEST_TEMPLATE_DATA, get_initialized_test_event


@pytest.mark.django_db
def test_email_action():
    if settings.EMAIL_BACKEND != "django.core.mail.backends.locmem.EmailBackend":
        pytest.skip("Need locmem email backend")

    mail.outbox = []  # Clear the Django testing mail outbox

    event = get_initialized_test_event()
    ctx = Context.from_event(event, shop=factories.get_default_shop())
    ctx.set("name", "Luke Warm")  # This variable isn't published by the event, but it's used by the template
    se = SendEmail(
        {
            "template_data": TEST_TEMPLATE_DATA,
            "from_email": {"constant": "from@shuup.local"},
            "recipient": {"constant": "someone@shuup.local"},
            "language": {"constant": "ja"},
            "send_identifier": {"constant": "hello, hello, hello"},
        }
    )
    se.execute(ctx)  # Once,
    se.execute(ctx)  # Twice!
    assert len(mail.outbox) == 1  # 'send_identifier' should ensure this is true
    msg = mail.outbox[0]
    assert msg.to == ["someone@shuup.local"]
    assert msg.from_email == "from@shuup.local"
    assert ctx.get("name").upper() in msg.subject  # The Japanese template upper-cases the name


@pytest.mark.django_db
def test_complete_email_action():
    if settings.EMAIL_BACKEND != "django.core.mail.backends.locmem.EmailBackend":
        pytest.skip("Need locmem email backend")

    mail.outbox = []  # Clear the Django testing mail outbox

    event = get_initialized_test_event()
    ctx = Context.from_event(event, shop=factories.get_default_shop())
    ctx.set("name", "Luke Warm")  # This variable isn't published by the event, but it's used by the template
    se = SendEmail(
        {
            "template_data": TEST_TEMPLATE_DATA,
            "from_email": {"constant": "from@shuup.local"},
            "recipient": {"constant": "someone@shuup.local,anotheremail@shuup.local"},
            "bcc": {"constant": "hiddenone@shuup.local,secret@shuup.local"},
            "cc": {"constant": "copied@shuup.local,loop@shuup.local"},
            "language": {"constant": "ja"},
            "send_identifier": {"constant": "hello, hello, hello"},
        }
    )
    se.execute(ctx)  # Once,
    se.execute(ctx)  # Twice!
    assert len(mail.outbox) == 1  # 'send_identifier' should ensure this is true
    msg = mail.outbox[0]
    assert msg.to == ["someone@shuup.local", "anotheremail@shuup.local"]
    assert msg.cc == ["copied@shuup.local", "loop@shuup.local"]
    assert msg.bcc == ["hiddenone@shuup.local", "secret@shuup.local"]
    assert msg.from_email == "from@shuup.local"
    assert ctx.get("name").upper() in msg.subject  # The Japanese template upper-cases the name


@pytest.mark.django_db
def test_email_action_with_template_body():
    with override_settings(LANGUAGES=(("en", "en"))):
        email_template = EmailTemplate.objects.create(
            name="template 1", template="<html><style>.dog-color { color: red; }</style><body>%html_body%</body></html>"
        )
        SUPER_TEST_TEMPLATE_DATA = {
            "en": {
                # English
                "subject": "Hello, {{ name }}!",
                "email_template": str(email_template.pk),
                "body": "Hi, {{ name }}. This is a test &amp; it works.",
                "content_type": "plain",
            }
        }

        if settings.EMAIL_BACKEND != "django.core.mail.backends.locmem.EmailBackend":
            pytest.skip("Need locmem email backend")

        mail.outbox = []  # Clear the Django testing mail outbox

        with mock.patch.object(notification_email_before_send, "send") as mocked_method_1:
            event = get_initialized_test_event()
            ctx = Context.from_event(event, shop=factories.get_default_shop())
            ctx.set("name", "John Smith")  # This variable isn't published by the event, but it's used by the template
            se = SendEmail(
                {
                    "template_data": SUPER_TEST_TEMPLATE_DATA,
                    "from_email": {"constant": "from@shuup.local"},
                    "recipient": {"constant": "someone@shuup.local"},
                    "language": {"constant": "ja"},
                }
            )
            assert ctx.event_identifier == "test_event"
            se.execute(ctx)
            mail.outbox[0].body == "Hi, John Smith. This is a test & it works."

        mocked_method_1.assert_called()

        mail.outbox = []  # Clear the Django testing mail outbox

        with mock.patch.object(notification_email_sent, "send") as mocked_method_2:
            event = get_initialized_test_event()
            ctx = Context.from_event(event, shop=factories.get_default_shop())
            ctx.set("name", "Luke J. Warm")  # This variable isn't published by the event, but it's used by the template
            se = SendEmail(
                {
                    "template_data": SUPER_TEST_TEMPLATE_DATA,
                    "from_email": {"constant": "from@shuup.local"},
                    "recipient": {"constant": "someone@shuup.local"},
                    "language": {"constant": "ja"},
                }
            )
            se.execute(ctx)  # Once
            assert len(mail.outbox) == 1  # 'send_identifier' should ensure this is true
            msg = mail.outbox[0]
            assert msg.to == ["someone@shuup.local"]
            assert msg.from_email == "from@shuup.local"
            assert ".dog-color { color: red; }" in msg.body
            assert "Luke J. Warm" in msg.body

        mocked_method_2.assert_called()
