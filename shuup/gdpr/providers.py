# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from shuup.front.providers import (
    FormDefinition, FormDefProvider, FormFieldDefinition, FormFieldProvider
)
from shuup.gdpr.forms import CompanyAgreementForm
from shuup.gdpr.models import GDPRSettings
from shuup.gdpr.utils import get_active_consent_pages
from shuup.utils.djangoenv import has_installed


class GDPRFormDefProvider(FormDefProvider):

    def get_definitions(self, **kwargs):
        from shuup.gdpr.models import GDPRSettings
        if not GDPRSettings.get_for_shop(self.request.shop).enabled:
            return []
        return [FormDefinition('agreement', CompanyAgreementForm, required=True)]


class GDPRFieldProvider(FormFieldProvider):
    error_message = ""

    def get_fields(self, **kwargs):
        request = kwargs.get("request", None)

        if not has_installed("shuup.gdpr") or not request:
            return []

        gdpr_settings = GDPRSettings.get_for_shop(request.shop)
        if not gdpr_settings.enabled:
            return []

        fields = []
        for page in get_active_consent_pages(request.shop):
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
    error_message = _("You must accept to this to register.")


class GDPRCheckoutFieldProvider(GDPRFieldProvider):
    error_message = _("You must accept to this to order.")


class GDPRAuthFieldProvider(GDPRFieldProvider):
    error_message = _("You must accept to this to authenticate.")
