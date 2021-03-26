# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.template import loader
from django.utils import translation
from django.utils.encoding import force_text

from shuup import configuration
from shuup.admin.utils import wizard
from shuup.admin.views.wizard import WizardView
from shuup.notify.actions.email import SendEmail
from shuup.notify.models import Script
from shuup.notify.script import StepNext
from shuup.simple_cms.models import Page
from shuup.testing.factories import get_default_shop
from shuup.testing.modules.content import data
from shuup.testing.modules.content.forms import (
    BEHAVIOR_ORDER_CONFIRM_KEY,
    CONTENT_FOOTER_KEY,
    BehaviorWizardForm,
    ContentWizardForm,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup.xtheme import XTHEME_GLOBAL_VIEW_NAME
from shuup.xtheme.models import SavedViewConfig, SavedViewConfigStatus


@pytest.mark.django_db
def test_behavior_form():
    shop = get_default_shop()

    assert Script.objects.count() == 0
    assert configuration.get(shop, BEHAVIOR_ORDER_CONFIRM_KEY) is None

    form = BehaviorWizardForm(shop=shop, data={"order_confirm_notification": True})
    assert form._get_saved_script() is None
    form.save()

    # check if the form creates a order notification correctely
    script = Script.objects.first()
    assert script.pk == configuration.get(shop, BEHAVIOR_ORDER_CONFIRM_KEY)
    assert form._get_saved_script().pk == script.pk
    assert len(script.get_steps()) == 1
    step = script.get_steps()[0]
    step_data = step.serialize()
    assert step_data["next"] == StepNext.STOP.value
    action = step._actions[0]
    assert isinstance(action, SendEmail)
    action_data = action.serialize()
    assert action_data["recipient"]["variable"] == "customer_email"
    assert action_data["language"]["variable"] == "language"
    lang = translation.get_language()
    assert action_data["fallback_language"]["constant"] == lang
    assert action_data["template_data"][lang]["content_type"] == "html"
    assert action_data["template_data"][lang]["subject"] == force_text(data.ORDER_CONFIRMATION["subject"])
    context = {"shop": shop}
    content = loader.render_to_string(data.ORDER_CONFIRMATION["body_template"], context).strip()
    assert action_data["template_data"][lang]["body"] == content

    # the widget must be disabled
    form = BehaviorWizardForm(shop=shop, data={"order_confirm_notification": True})
    assert form.fields["order_confirm_notification"].widget.attrs["disabled"] is True

    # clear scripts
    Script.objects.all().delete()
    configuration.set(shop, BEHAVIOR_ORDER_CONFIRM_KEY, None)

    # save the form but do not create the order confirmation notification
    form = BehaviorWizardForm(shop=shop, data={"order_confirm_notification": False})
    form.save()

    # nothing created
    assert Script.objects.count() == 0
    assert configuration.get(shop, BEHAVIOR_ORDER_CONFIRM_KEY) is None


@pytest.mark.django_db
def test_content_form(settings):
    shop = get_default_shop()

    # check for fields existence
    form = ContentWizardForm(shop=shop)
    assert "about_us" in form.fields
    assert "privacy_policy" in form.fields
    assert "terms_conditions" in form.fields
    assert "refund_policy" in form.fields
    assert "configure_footer" in form.fields

    # remove simple cms from settings
    settings.INSTALLED_APPS.remove("shuup.simple_cms")
    form = ContentWizardForm(shop=shop)
    assert "about_us" not in form.fields
    assert "privacy_policy" not in form.fields
    assert "terms_conditions" not in form.fields
    assert "refund_policy" not in form.fields
    assert "configure_footer" in form.fields

    # remove xtheme from settings
    settings.INSTALLED_APPS.remove("shuup.xtheme")
    form = ContentWizardForm(shop=shop)
    assert "about_us" not in form.fields
    assert "privacy_policy" not in form.fields
    assert "terms_conditions" not in form.fields
    assert "refund_policy" not in form.fields
    assert "configure_footer" not in form.fields

    assert Page.objects.count() == 0
    assert SavedViewConfig.objects.count() == 0

    settings.INSTALLED_APPS.append("shuup.simple_cms")
    settings.INSTALLED_APPS.append("shuup.xtheme")

    context = {"shop": shop}

    # create about_us page
    form = ContentWizardForm(shop=shop, data={data.ABOUT_US_KEY: True})
    form.save()
    assert Page.objects.count() == 1
    assert SavedViewConfig.objects.count() == 0
    about_us_page = Page.objects.get(identifier=data.ABOUT_US_KEY)
    assert about_us_page.title == data.CMS_PAGES[data.ABOUT_US_KEY]["name"]
    content = loader.render_to_string(data.CMS_PAGES[data.ABOUT_US_KEY]["template"], context).strip()
    assert about_us_page.content == content
    assert about_us_page.available_from is not None

    # create privacy_policy page
    form = ContentWizardForm(shop=shop, data={data.PRIVACY_POLICY_KEY: True})
    form.save()
    assert Page.objects.count() == 2
    assert SavedViewConfig.objects.count() == 0
    priv_poli_page = Page.objects.get(identifier=data.PRIVACY_POLICY_KEY)
    assert priv_poli_page.title == data.CMS_PAGES[data.PRIVACY_POLICY_KEY]["name"]
    content = loader.render_to_string(data.CMS_PAGES[data.PRIVACY_POLICY_KEY]["template"], context).strip()
    assert priv_poli_page.content == content
    assert priv_poli_page.available_from is not None

    # create refund page
    form = ContentWizardForm(shop=shop, data={data.REFUND_POLICY_KEY: True})
    form.save()
    assert Page.objects.count() == 3
    assert SavedViewConfig.objects.count() == 0
    refund_page = Page.objects.get(identifier=data.REFUND_POLICY_KEY)
    assert refund_page.title == data.CMS_PAGES[data.REFUND_POLICY_KEY]["name"]
    content = loader.render_to_string(data.CMS_PAGES[data.REFUND_POLICY_KEY]["template"], context).strip()
    assert refund_page.content == content
    assert refund_page.available_from is not None

    # create terms page
    form = ContentWizardForm(shop=shop, data={data.TERMS_AND_CONDITIONS_KEY: True})
    form.save()
    assert Page.objects.count() == 4
    assert SavedViewConfig.objects.count() == 0
    terms_page = Page.objects.get(identifier=data.TERMS_AND_CONDITIONS_KEY)
    assert terms_page.title == data.CMS_PAGES[data.TERMS_AND_CONDITIONS_KEY]["name"]
    content = loader.render_to_string(data.CMS_PAGES[data.TERMS_AND_CONDITIONS_KEY]["template"], context).strip()
    assert terms_page.content == content
    assert terms_page.available_from is not None

    # create the footer
    form = ContentWizardForm(shop=shop, data={"configure_footer": True})
    form.save()
    assert Page.objects.count() == 4
    assert SavedViewConfig.objects.count() == 1
    svc = SavedViewConfig.objects.first()
    assert configuration.get(shop, CONTENT_FOOTER_KEY) == svc.pk
    assert svc.shop == shop
    assert svc.view_name == XTHEME_GLOBAL_VIEW_NAME
    assert svc.status == SavedViewConfigStatus.PUBLIC
    content = loader.render_to_string(data.FOOTER_TEMPLATE, context).strip()
    assert svc.get_layout_data("footer-bottom")["rows"][0]["cells"][0]["plugin"] == "snippets"
    assert svc.get_layout_data("footer-bottom")["rows"][0]["cells"][0]["config"]["in_place"] == content


@pytest.mark.django_db
def test_content_wizard_pane(rf, admin_user, settings):
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = ["shuup.testing.modules.content.views.ContentWizardPane"]
    shop = get_default_shop()

    pane_data = {
        "pane_id": "content",
        "content-privacy_policy": False,
        "content-terms_conditions": False,
        "content-refund_policy": False,
        "content-about_us": False,
        "content-configure_footer": False,
        "behaviors-order_confirm_notification": False,
    }

    # all false, does not create anything
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 0
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 0

    # create privacy policy
    pane_data["content-privacy_policy"] = True
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 1
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 0

    # create terms
    pane_data["content-terms_conditions"] = True
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 2
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 0

    # create refund
    pane_data["content-refund_policy"] = True
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 3
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 0

    # create about_us
    pane_data["content-about_us"] = True
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 4
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 0

    # create footer
    pane_data["content-configure_footer"] = True
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 4
    assert SavedViewConfig.objects.count() == 1
    assert Script.objects.count() == 0

    # create order_confirm_notification
    pane_data["behaviors-order_confirm_notification"] = True
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 4
    assert SavedViewConfig.objects.count() == 1
    assert Script.objects.count() == 1

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:dashboard")


@pytest.mark.django_db
def test_content_wizard_pane2(rf, admin_user, settings):
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = ["shuup.testing.modules.content.views.ContentWizardPane"]

    shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    settings.INSTALLED_APPS.remove("shuup.simple_cms")
    settings.INSTALLED_APPS.remove("shuup.xtheme")
    settings.INSTALLED_APPS.remove("shuup.notify")

    # no pane, because ContentWizardPane is invalid (no necessary app installed)
    assert wizard.load_setup_wizard_panes(shop, request) == []
    assert wizard.load_setup_wizard_panes(shop, request, visible_only=False) == []
    pane_data = {
        "pane_id": "content",
        "content-privacy_policy": True,
        "content-terms_conditions": True,
        "content-refund_policy": True,
        "content-about_us": True,
        "content-configure_footer": True,
        "behaviors-order_confirm_notification": True,
    }

    request = apply_request_middleware(rf.get("/"), skip_session=True)
    response = WizardView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("shuup:login"))

    # add the simple cms - create only the pages and footer
    request = apply_request_middleware(rf.get("/"), user=admin_user, skip_session=True)
    settings.INSTALLED_APPS.append("shuup.simple_cms")
    assert len(wizard.load_setup_wizard_panes(shop, request, visible_only=False)) == 1
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 4
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 0
    settings.INSTALLED_APPS.remove("shuup.simple_cms")
    Page.objects.all().delete()

    # add the xtheme - create the footer
    settings.INSTALLED_APPS.append("shuup.xtheme")
    assert len(wizard.load_setup_wizard_panes(shop, request, visible_only=False)) == 1
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 0
    assert SavedViewConfig.objects.count() == 1
    assert Script.objects.count() == 0
    settings.INSTALLED_APPS.remove("shuup.xtheme")
    SavedViewConfig.objects.all().delete()

    # add the notify - create only the notification
    settings.INSTALLED_APPS.append("shuup.notify")
    assert len(wizard.load_setup_wizard_panes(shop, request, visible_only=False)) == 1
    request = apply_request_middleware(rf.post("/", data=pane_data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200
    assert Page.objects.count() == 0
    assert SavedViewConfig.objects.count() == 0
    assert Script.objects.count() == 1
    settings.INSTALLED_APPS.remove("shuup.notify")
    Script.objects.all().delete()

    settings.INSTALLED_APPS.append("shuup.simple_cms")
    settings.INSTALLED_APPS.append("shuup.xtheme")
    settings.INSTALLED_APPS.append("shuup.notify")
