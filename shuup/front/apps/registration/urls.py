# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import patterns, url

from .views import (
    activation_complete, ActivationView, registration_complete,
    RegistrationView
)

urlpatterns = patterns(
    '',
    url(r'^activate/complete/$', activation_complete, name='registration_activation_complete'),
    url(r'^activate/(?P<activation_key>\w+)/$', ActivationView.as_view(), name='registration_activate'),
    url(r'^register/$', RegistrationView.as_view(), name='registration_register'),
    url(r'^register/complete/$', registration_complete, name='registration_complete'),
)
