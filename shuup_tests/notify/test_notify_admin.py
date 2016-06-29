# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.notify.actions.email import SendEmail
from shuup.notify.admin_module.forms import ScriptItemEditForm
from shuup_tests.notify.fixtures import ATestEvent


# TODO: Embetter the tests in this file

def test_notify_item_admin_form():
    event_class = ATestEvent
    script_item = SendEmail({
        "send_identifier": {"constant": "hello"},
        "recipient": {"constant": "hello@shuup.local"},
        "language": {"constant": "en"},
    })
    form = ScriptItemEditForm(
        event_class=event_class,
        script_item=script_item,
        data={
            "b_recipient_c": "konnichiwa@jp.shuup.local",
            "b_language_c": "en",
            "b_send_identifier_c": "hello",
        }
    )
    initial = form.get_initial()
    assert initial["b_send_identifier_c"] == "hello"
    assert form.is_valid()

    form.save()
    assert script_item.data["recipient"] == {"constant": "konnichiwa@jp.shuup.local"}
