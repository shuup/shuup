# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django.contrib.auth.views as auth_views

from shuup.utils.importing import cached_load


class LogoutView(auth_views.LogoutView):
    template_name = "shuup/admin/auth/logout.jinja"


class LoginView(auth_views.LoginView):
    form_class = cached_load("SHUUP_ADMIN_AUTH_FORM_SPEC")
