# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.http.response import Http404
from django.test.utils import override_settings

from shuup.admin.shop_provider import set_shop
from shuup.notify.actions.email import SendEmail
from shuup.notify.admin_module.forms import ScriptItemEditForm
from shuup.notify.admin_module.views import ScriptEditView
from shuup.notify.models import Script
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
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


@pytest.mark.django_db
def test_admin_script_list(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = factories.get_shop(identifier="shop-1", enabled=True)
        shop2 = factories.get_shop(identifier="shop-2", enabled=True)

        shop1.staff_members.add(admin_user)
        shop2.staff_members.add(admin_user)

        script_shop1 = Script.objects.create(shop=shop1, event_identifier="order_received", name="SHOP 1", enabled=True)
        script_shop2 = Script.objects.create(shop=shop2, event_identifier="order_received", name="SHOP 2", enabled=True)

        view = ScriptEditView.as_view()
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        set_shop(request, shop2)

        with pytest.raises(Http404):
            response = view(request, pk=script_shop1.id)

        response = view(request, pk=script_shop2.id)
        assert response.status_code == 200
