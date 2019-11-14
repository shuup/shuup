# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from shuup.front.providers import (
    FormDefinition, FormDefProvider, FormFieldDefinition, FormFieldProvider
)
from shuup.gdpr.forms import CompanyAgreementForm
from shuup.gdpr.models import GDPRSettings, GDPRUserConsent
from shuup.gdpr.utils import get_active_consent_pages
from shuup.utils.django_compat import is_authenticated, reverse
from shuup.utils.djangoenv import has_installed


class TextOnlyWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(self.attrs.get("value", ""))


class GDPRFormDefProvider(FormDefProvider):

    def get_definitions(self, **kwargs):
        from shuup.gdpr.models import GDPRSettings
        if not GDPRSettings.get_for_shop(self.request.shop).enabled:
            return []
        return [FormDefinition('agreement', CompanyAgreementForm, required=True)]


def get_gdpr_settings(request):
    if not has_installed("shuup.gdpr") or not request:
        return None

    gdpr_settings = GDPRSettings.get_for_shop(request.shop)
    return (gdpr_settings if gdpr_settings.enabled else None)


class GDPRFieldProvider(FormFieldProvider):
    error_message = ""

    def get_fields(self, **kwargs):
        request = kwargs.get("request", None)
        gdpr_settings = get_gdpr_settings(request)
        if not gdpr_settings:
            return []

        user_consent = None
        if is_authenticated(request.user):
            user_consent = GDPRUserConsent.get_for_user(request.user, request.shop)

        fields = []
        for page in get_active_consent_pages(request.shop):
            # user already has consented to this page, ignore it
            if user_consent and not user_consent.should_reconsent_to_page(page):
                continue

            key = "accept_{}".format(page.id)
            field = forms.BooleanField(
                label=mark_safe(ugettext(
                    "I have read and accept the <a href='{}' target='_blank' class='gdpr_consent_doc_check'>{}</a>"
                ).format(reverse("shuup:cms_page", kwargs=dict(url=page.url)), page.title)),
                required=True,
                error_messages=dict(required=self.error_message)
            )
            definition = FormFieldDefinition(name=key, field=field)
            fields.append(definition)
        return fields


class GDPRRegistrationFieldProvider(GDPRFieldProvider):
    error_message = _("You must accept this in order to register.")


class GDPRCheckoutFieldProvider(GDPRFieldProvider):
    error_message = _("You must accept this to order.")


class GDPRAuthFieldProvider(GDPRFieldProvider):
    error_message = _("You must accept this in order to authenticate.")

    def get_fields(self, **kwargs):
        request = kwargs.get("request", None)
        gdpr_settings = get_gdpr_settings(request)
        if not gdpr_settings:
            return []

        if gdpr_settings.skip_consent_on_auth:
            auth_consent_text = gdpr_settings.safe_translation_getter("auth_consent_text")
            return [
                FormFieldDefinition(
                    name="auth_consent_text",
                    field=forms.CharField(
                        label="",
                        initial="",
                        required=False,
                        widget=TextOnlyWidget(attrs={"value": auth_consent_text})
                    )
                )
            ]
        else:
            return super(GDPRAuthFieldProvider, self).get_fields(**kwargs)
