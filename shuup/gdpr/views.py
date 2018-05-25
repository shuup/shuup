# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import re

from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.http import (
    HttpResponse, HttpResponseNotFound, HttpResponseRedirect
)
from django.views.generic import TemplateView, View

from shuup.core.models import Order
from shuup.gdpr.anonymizer import Anonymizer
from shuup.gdpr.models import GDPRCookieCategory
from shuup.gdpr.utils import (
    add_consent_to_response_cookie, get_cookie_consent_data
)
from shuup.utils.analog import LogEntryKind
from shuup.utils.djangoenv import has_installed

COOKIE_CONSENT_RE = r"cookie_category_(\d+)"


class GDPRConsentView(View):
    def post(self, request, *args, **kwargs):
        shop = request.shop
        cookie_categories = list(GDPRCookieCategory.objects.filter(shop=shop, always_active=True))

        for field, value in request.POST.items():
            field_match = re.match(COOKIE_CONSENT_RE, field)
            if field_match and value.lower() in ["on", "1"]:
                cookie_category = GDPRCookieCategory.objects.filter(shop=shop, id=field_match.groups()[0]).first()
                if cookie_category:
                    cookie_categories.append(cookie_category)

        consent_documents = []
        if has_installed("shuup.simple_cms"):
            from shuup.simple_cms.models import Page, PageType
            consent_documents = Page.objects.visible(shop).filter(page_type=PageType.GDPR_CONSENT_DOCUMENT)

        cookie_data = get_cookie_consent_data(cookie_categories, consent_documents)

        if request.META.get("HTTP_REFERER"):
            redirect_url = request.META["HTTP_REFERER"]
        else:
            redirect_url = reverse("shuup:index")

        response = HttpResponseRedirect(redirect_url)
        add_consent_to_response_cookie(response, cookie_data)
        return response


class GDPRCustomerDashboardView(TemplateView):
    template_name = "shuup/gdpr/edit_customer_data.jinja"

    def get_context_data(self, **kwargs):
        context = super(GDPRCustomerDashboardView, self).get_context_data(**kwargs)
        has_peding_orders = False

        if Order.objects.incomplete().filter(customer=self.request.person).exists():
            has_peding_orders = True
        else:
            for company in self.request.person.company_memberships.all():
                if company.members.count() == 1:
                    has_peding_orders = True

        context["has_peding_orders"] = has_peding_orders
        return context


class GDPRDownloadDataView(View):
    def post(self, request, *args, **kwargs):
        if not self.request.person:
            return HttpResponseNotFound()

        self.request.person.add_log_entry(
            "User personal data download requested", kind=LogEntryKind.NOTE, user=self.request.user)

        from shuup.gdpr.utils import get_all_contact_data
        data = json.dumps(get_all_contact_data(self.request.person))
        response = HttpResponse(data, content_type="application/json")
        response["Content-Disposition"] = "attachment; filename=user_data.json"
        return response


class GDPRAnonymizeView(View):
    def post(self, request, *args, **kwargs):
        if not self.request.person:
            return HttpResponseNotFound()

        self.request.person.add_log_entry(
            "User anonymization requested", kind=LogEntryKind.NOTE, user=self.request.user)

        with atomic():
            anonymizer = Anonymizer()
            anonymizer.anonymize_person(self.request.person)

            # check if there is any company related to the person
            # if so, anonymize it if he is the unique member
            for company in self.request.person.company_memberships.all():
                if company.members.count() == 1:
                    anonymizer.anonymize_company(company)

                    # cancel company orders
                    for order in Order.objects.incomplete().filter(customer=company):
                        order.set_canceled()

            if hasattr(self.request.person, "user"):
                anonymizer.anonymize_user(self.request.person.user)

            for order in Order.objects.incomplete().filter(customer=self.request.person):
                order.set_canceled()

        return HttpResponseRedirect(reverse("shuup:index"))
