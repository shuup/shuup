# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import CompanyContact, Contact, PersonContact
from shuup.gdpr.admin_module.forms import (
    GDPRBaseFormPart, GDPRCookieCategoryFormPart
)
from shuup.gdpr.anonymizer import Anonymizer
from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings
from shuup.gdpr.utils import (
    create_initial_required_cookie_category, ensure_gdpr_privacy_policy
)
from shuup.utils.analog import LogEntryKind


class GDPRView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = GDPRSettings
    template_name = "shuup/admin/gdpr/edit.jinja"
    base_form_part_classes = [GDPRBaseFormPart, GDPRCookieCategoryFormPart]
    success_url = reverse_lazy("shuup_admin:gdpr.settings")

    def get_toolbar(self):
        toobar = Toolbar([
            PostActionButton(
                icon="fa fa-check-circle",
                form_id="gdpr_form",
                text=_("Save"),
                extra_css_class="btn-success",
            )
        ], view=self)
        return toobar

    def get_queryset(self):
        return GDPRSettings.objects.filter(shop=get_shop(self.request))

    def get_object(self):
        return GDPRSettings.get_for_shop(get_shop(self.request))

    def get_context_data(self, **kwargs):
        context = super(GDPRView, self).get_context_data(**kwargs)
        context["title"] = _("General Data Protection Regulation")
        context["toolbar"] = self.get_toolbar()
        return context

    def form_valid(self, form):
        result = self.save_form_parts(form)

        gdpr_settings = self.get_object()
        if gdpr_settings.enabled:
            ensure_gdpr_privacy_policy(self.object.shop)
            if not GDPRCookieCategory.objects.filter(shop=gdpr_settings.shop).exists():
                create_initial_required_cookie_category(self.object.shop)
        return result


class BaseContactView(SingleObjectMixin, View):
    def get_queryset(self):
        queryset = Contact.objects.all()

        limited = (settings.SHUUP_ENABLE_MULTIPLE_SHOPS and settings.SHUUP_MANAGE_CONTACTS_PER_SHOP and
                   not self.request.user.is_superuser)
        if limited:
            queryset = queryset.filter(shops=get_shop(self.request))

        return queryset


class GDPRDownloadDataView(BaseContactView):
    def post(self, request, *args, **kwargs):
        contact = self.get_object()
        contact.add_log_entry("User personal data download requested", kind=LogEntryKind.NOTE, user=self.request.user)
        from shuup.gdpr.utils import get_all_contact_data
        data = json.dumps(get_all_contact_data(contact))
        response = HttpResponse(data, content_type="application/json")
        filename = "attachment; filename=user_data_{}.json".format(now().strftime("%Y-%m-%d_%H:%M:%S"))
        response["Content-Disposition"] = filename
        return response


class GDPRAnonymizeView(BaseContactView):
    def post(self, request, *args, **kwargs):
        contact = self.get_object()
        contact.add_log_entry("User anonymization requested", kind=LogEntryKind.NOTE, user=self.request.user)
        with atomic():
            anonymizer = Anonymizer()
            if isinstance(contact, PersonContact):
                anonymizer.anonymize_person(contact)
            elif isinstance(contact, CompanyContact):
                anonymizer.anonymize_company(contact)

        messages.success(request, _("Contact anonymized!"))
        return HttpResponseRedirect(reverse("shuup_admin:contact.detail", kwargs=dict(pk=contact.pk)))
