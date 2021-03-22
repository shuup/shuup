# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django import forms
from django.http.response import Http404
from django.test.utils import override_settings

from shuup.admin.shop_provider import set_shop
from shuup.notify.actions.email import SendEmail
from shuup.notify.admin_module.forms import ScriptItemEditForm
from shuup.notify.admin_module.views import ScriptEditView, script_item_editor
from shuup.notify.admin_module.views.delete import ScriptDeleteView
from shuup.notify.models import Script
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import force_text, reverse
from shuup_tests.notify.fixtures import TEST_TEMPLATE_DATA, ATestEvent

# TODO: Embetter the tests in this file


@pytest.mark.django_db
def test_notify_item_admin_form(rf, admin_user):
    event_class = ATestEvent
    script_item = SendEmail(
        {
            "send_identifier": {"constant": "hello"},
            "recipient": {"constant": "hello@shuup.local"},
            "language": {"constant": "en"},
        }
    )
    send_data = {
        "b_recipient_c": "konnichiwa@jp.shuup.local",
        "b_language_c": "en",
        "b_message_c": "Message",
        "b_send_identifier_c": "hello",
        "t_en_subject": "Welcome!",
        "t_ja_subject": "Konnichiwa!",
        "t_ja_body": "Bye",
        "t_en_content_type": "html",
    }
    form = ScriptItemEditForm(event_class=event_class, script_item=script_item, data=send_data)
    initial = form.get_initial()
    assert initial["b_send_identifier_c"] == "hello"
    assert not form.is_valid()  # Missing template body for default language
    with pytest.raises(forms.ValidationError):
        form.save()

    send_data.update({"t_en_body": "ok now this should pass"})
    form = ScriptItemEditForm(event_class=event_class, script_item=script_item, data=send_data)
    initial = form.get_initial()
    assert initial["b_send_identifier_c"] == "hello"
    assert form.is_valid()
    form.save()

    assert script_item.data["template_data"]["en"]["subject"] == "Welcome!"
    assert script_item.data["template_data"]["ja"]["subject"] == "Konnichiwa!"
    assert script_item.data["recipient"] == {"constant": "konnichiwa@jp.shuup.local"}
    send_data["b_recipient_c"] = admin_user.pk
    send_data["init_data"] = json.dumps(
        {"eventIdentifier": "order_received", "itemType": "action", "data": {"identifier": "add_notification"}}
    )
    view = script_item_editor
    request = apply_request_middleware(rf.post("/", data=send_data), user=admin_user)
    response = view(request)
    assert response.status_code == 200  #  Assert no errors have occurred


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


@pytest.mark.django_db
def test_deleting_script(rf, admin_user):
    shop = factories.get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    script = Script.objects.create(shop=shop, event_identifier="order_received", name="Script 1", enabled=True)

    delete_url = reverse("shuup_admin:notify.script.delete", kwargs={"pk": script.pk})
    view = ScriptEditView.as_view()
    response = view(request, pk=script.pk).render()
    assert bool(delete_url in force_text(response.content))

    assert Script.objects.count() == 1

    request = apply_request_middleware(rf.post("/"), user=admin_user)
    delete_view = ScriptDeleteView.as_view()
    response = delete_view(request, pk=script.pk)
    assert response.status_code == 302  # Redirect to list view
    assert Script.objects.count() == 0
