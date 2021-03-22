# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.template.defaultfilters import linebreaksbr
from django.utils.translation import activate

from shuup.apps.provides import override_provides
from shuup.front.apps.registration.notify_events import RegistrationReceivedEmailScriptTemplate
from shuup.front.notify_script_templates.generics import (
    OrderConfirmationEmailScriptTemplate,
    PaymentCreatedEmailScriptTemplate,
    RefundCreatedEmailScriptTemplate,
    ShipmentCreatedEmailScriptTemplate,
    ShipmentDeletedEmailScriptTemplate,
)
from shuup.notify.admin_module.views import ScriptTemplateConfigView, ScriptTemplateEditView, ScriptTemplateView
from shuup.notify.models import Script
from shuup.notify.script_templates import PasswordResetTemplate
from shuup.simple_supplier.notify_events import AlertLimitReached
from shuup.simple_supplier.notify_script_template import StockLimitEmailScriptTemplate
from shuup.testing.factories import get_default_shop
from shuup.testing.notify_script_templates import DummyScriptTemplate
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


def setup_function(fn):
    activate("en")


def _assert_generic_script(script_template_cls, script, data):
    serialized_steps = script.get_serialized_steps()
    assert script.event_identifier == script_template_cls.event.identifier
    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert len(serialized_steps[0]["conditions"]) == 0
    assert serialized_steps[0]["actions"][0]["recipient"]["variable"] == "customer_email"

    for lang, _ in settings.LANGUAGES:
        assert serialized_steps[0]["actions"][0]["template_data"][lang].get("body") == data.get("%s-body" % lang, "")
        assert serialized_steps[0]["actions"][0]["template_data"][lang].get("subject") == data.get(
            "%s-subject" % lang, ""
        )


def _assert_stock_alert_limit_script(script, data):
    serialized_steps = script.get_serialized_steps()
    assert script.event_identifier == AlertLimitReached.identifier
    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert serialized_steps[0]["actions"][0]["recipient"]["constant"] == data["base-recipient"]

    if data["base-last24hrs"]:
        assert len(serialized_steps[0]["conditions"]) == 1
        assert serialized_steps[0]["conditions"][0]["v1"]["variable"] == "dispatched_last_24hs"
        assert serialized_steps[0]["conditions"][0]["v2"]["constant"] == (not data["base-last24hrs"])
    else:
        assert serialized_steps[0]["conditions"] == []

    for lang, _ in settings.LANGUAGES:
        assert serialized_steps[0]["actions"][0]["template_data"][lang].get("body") == data.get("%s-body" % lang, "")
        assert serialized_steps[0]["actions"][0]["template_data"][lang].get("subject") == data.get(
            "%s-subject" % lang, ""
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "script_template_cls",
    [
        OrderConfirmationEmailScriptTemplate,
        PaymentCreatedEmailScriptTemplate,
        RefundCreatedEmailScriptTemplate,
        ShipmentCreatedEmailScriptTemplate,
        ShipmentDeletedEmailScriptTemplate,
        RegistrationReceivedEmailScriptTemplate,
        PasswordResetTemplate,
    ],
)
def test_generic_script_template_manual(script_template_cls):
    shop = get_default_shop()
    script_template = script_template_cls()
    form = script_template.get_form()
    initial = script_template.get_initial()
    for k, v in form.initial.items():
        assert initial[k] == v

    data = {
        "base-send_to": "customer",
        "en-body": "my body",
        "en-subject": "something",
        "fi-body": "my body FI",
        "fi-subject": "something FI",
    }
    form = script_template.get_form(data=data)
    assert form.is_valid()

    script = script_template.create_script(shop, form)
    assert script is not None
    _assert_generic_script(script_template_cls, script, data)

    # edit
    script_template = script_template_cls(script)
    assert script_template.can_edit_script()
    data.update({"base-send_to": "customer", "en-body": "my body 2", "en-subject": "something 2"})
    form = script_template.get_form(data=data)
    assert form.is_valid()
    edited_script = script_template.update_script(form)
    _assert_generic_script(script_template_cls, edited_script, data)
    script.refresh_from_db()
    _assert_generic_script(script_template_cls, script, data)

    # invalidate script so we can't edit it anymore
    script.set_steps([])
    script.save()
    script_template = script_template_cls(script)
    assert not script_template.can_edit_script()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "script_template_cls",
    [
        OrderConfirmationEmailScriptTemplate,
        PaymentCreatedEmailScriptTemplate,
        RefundCreatedEmailScriptTemplate,
        ShipmentCreatedEmailScriptTemplate,
        ShipmentDeletedEmailScriptTemplate,
        RegistrationReceivedEmailScriptTemplate,
    ],
)
def test_generic_script_template_admin(rf, admin_user, script_template_cls):
    get_default_shop()
    Script.objects.all().delete()
    identifier = script_template_cls.identifier

    # should redirect us since the script template has a bound form
    request = apply_request_middleware(rf.post("/", {"id": identifier}), user=admin_user)
    response = ScriptTemplateView.as_view()(request)
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:notify.script-template-config", kwargs={"id": identifier})
    assert Script.objects.count() == 0

    # create
    data = {
        "base-send_to": "customer",
        "en-body": "my body",
        "en-subject": "something",
        "fi-body": "my body FI",
        "fi-subject": "something FI",
    }
    request = apply_request_middleware(rf.post("/", data), user=admin_user)
    response = ScriptTemplateConfigView.as_view()(request, id=identifier)
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:notify.script.list")
    script = Script.objects.first()
    assert script is not None
    _assert_generic_script(script_template_cls, script, data)

    # edit
    data.update({"en-body": "my body 2", "en-subject": "something 2"})
    request = apply_request_middleware(rf.post("/", data), user=admin_user)
    response = ScriptTemplateEditView.as_view()(request, pk=script.pk)
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:notify.script.list")
    assert Script.objects.count() == 1
    edited_script = Script.objects.first()
    _assert_generic_script(script_template_cls, edited_script, data)


@pytest.mark.django_db
def test_stock_alert_limit_script_template_manual(rf):
    shop = get_default_shop()
    script_template = StockLimitEmailScriptTemplate()
    form = script_template.get_form()

    initial = script_template.get_initial()
    assert form["en"].initial["subject"] == initial["en-subject"]
    assert form["en"].initial["body"] == linebreaksbr(initial["en-body"])

    data = {
        "en-body": "my body",
        "en-subject": "something",
        "base-recipient": "someemail@shuup.com",
        "base-last24hrs": True,
    }
    form = script_template.get_form(data=data)
    assert form.is_valid()

    # create
    script = script_template.create_script(shop, form)
    assert script is not None
    _assert_stock_alert_limit_script(script, data)

    # edit
    script_template = StockLimitEmailScriptTemplate(script)
    assert script_template.can_edit_script()
    data.update(
        {
            "en-body": "my body 2",
            "en-subject": "something 2",
            "base-recipient": "someemail@shuup.comzzz",
        }
    )
    form = script_template.get_form(data=data)
    assert form.is_valid()
    edited_script = script_template.update_script(form)
    _assert_stock_alert_limit_script(edited_script, data)
    script.refresh_from_db()
    _assert_stock_alert_limit_script(script, data)

    # invalidate script so we can't edit it anymore
    script.set_steps([])
    script.save()
    script_template = StockLimitEmailScriptTemplate(script)
    assert not script_template.can_edit_script()


@pytest.mark.django_db
def test_stock_alert_limit_script_template_admin(rf, admin_user):
    get_default_shop()

    Script.objects.all().delete()
    identifier = StockLimitEmailScriptTemplate.identifier

    # should redirect us since the script template has a bound form
    request = apply_request_middleware(rf.post("/", {"id": identifier}), user=admin_user)
    response = ScriptTemplateView.as_view()(request)
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:notify.script-template-config", kwargs={"id": identifier})
    assert Script.objects.count() == 0

    # create
    data = {
        "en-body": "my body",
        "en-subject": "something",
        "base-recipient": "someemail@shuup.com",
        "base-last24hrs": True,
    }
    request = apply_request_middleware(rf.post("/", data), user=admin_user)
    response = ScriptTemplateConfigView.as_view()(request, id=identifier)
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:notify.script.list")
    script = Script.objects.first()
    assert script is not None
    _assert_stock_alert_limit_script(script, data)

    # edit
    data.update(
        {
            "en-body": "my body 2",
            "en-subject": "something 2",
            "base-recipient": "someemail@shuup.comzzz",
        }
    )
    request = apply_request_middleware(rf.post("/", data), user=admin_user)
    response = ScriptTemplateEditView.as_view()(request, pk=script.pk)
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:notify.script.list")
    assert Script.objects.count() == 1
    edited_script = Script.objects.first()
    _assert_stock_alert_limit_script(edited_script, data)


@pytest.mark.django_db
def test_dummy_script_template_manual(rf):

    with override_provides("notify_script_template", ["shuup.testing.notify_script_templates:DummyScriptTemplate"]):
        shop = get_default_shop()
        Script.objects.all().delete()

        script_template = DummyScriptTemplate()
        form = script_template.get_form()
        assert form is None

        script = script_template.create_script(shop)
        assert script is not None

        db_script = Script.objects.first()
        assert script.pk == db_script.pk

        serialized_steps = db_script.get_serialized_steps()

        assert len(serialized_steps) == 1
        assert len(serialized_steps[0]["actions"]) == 0
        assert len(serialized_steps[0]["conditions"]) == 1
        assert serialized_steps[0]["conditions"][0]["v1"]["constant"]
        assert not serialized_steps[0]["conditions"][0]["v2"]["constant"]


@pytest.mark.django_db
def test_dummy_script_template_admin(rf, admin_user):

    with override_provides("notify_script_template", ["shuup.testing.notify_script_templates:DummyScriptTemplate"]):
        get_default_shop()

        Script.objects.all().delete()
        request = apply_request_middleware(rf.post("/", {"id": DummyScriptTemplate.identifier}), user=admin_user)
        response = ScriptTemplateView.as_view()(request)
        assert response.status_code == 302
        assert response.url == reverse("shuup_admin:notify.script.list")

        script = Script.objects.first()
        assert script is not None

        serialized_steps = script.get_serialized_steps()
        assert len(serialized_steps) == 1
        assert len(serialized_steps[0]["actions"]) == 0
        assert len(serialized_steps[0]["conditions"]) == 1
        assert serialized_steps[0]["conditions"][0]["v1"]["constant"]
        assert not serialized_steps[0]["conditions"][0]["v2"]["constant"]
