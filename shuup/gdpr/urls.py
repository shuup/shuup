# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url

from .views import (
    GDPRAnonymizeView, GDPRCookieConsentView, GDPRCustomerDashboardView,
    GDPRDownloadDataView, GDPRPolicyConsentView
)

urlpatterns = [
    url(r'^gdpr/policy-consent/(?P<page_id>\d+)/$', GDPRPolicyConsentView.as_view(), name='gdpr_policy_consent'),
    url(r'^gdpr/consent/$', GDPRCookieConsentView.as_view(), name='gdpr_consent'),
    url(r'^gdpr/download_data/$', GDPRDownloadDataView.as_view(), name='gdpr_download_data'),
    url(r'^gdpr/anonymize/$', GDPRAnonymizeView.as_view(), name='gdpr_anonymize_account'),
    url(r'^gdpr/customer/$', GDPRCustomerDashboardView.as_view(), name='gdpr_customer_dashboard')
]
