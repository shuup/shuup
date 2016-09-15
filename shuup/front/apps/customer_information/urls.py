# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = patterns(
    '',
    url(r'^customer/$', login_required(views.CustomerEditView.as_view()),
        name='customer_edit'),
    url(r'^change-password/$', login_required(views.change_password),
        name='change_password'),
    url(r'^company/$', login_required(views.CompanyEditView.as_view()),
        name='company_edit'),
)
