# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url

from .views import ActivationView, CompanyRegistrationView, RegistrationView, activation_complete, registration_complete

urlpatterns = [
    url(r"^activate/complete/$", activation_complete, name="registration_activation_complete"),
    url(r"^activate/(?P<activation_key>\w+)/$", ActivationView.as_view(), name="registration_activate"),
    url(r"^register/$", RegistrationView.as_view(), name="registration_register"),
    url(r"^register/company/$", CompanyRegistrationView.as_view(), name="registration_register_company"),
    url(r"^register/complete/$", registration_complete, name="registration_complete"),
]
