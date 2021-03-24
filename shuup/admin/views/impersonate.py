# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib.auth import get_user_model, load_backend, login, logout
from django.http import HttpResponseForbidden, HttpResponseRedirect

from shuup.admin.utils.permissions import has_permission
from shuup.utils.django_compat import reverse


def stop_impersonating_staff(request):
    if "impersonator_user_id" not in request.session:
        return HttpResponseForbidden()

    impersonator_user_id = request.session["impersonator_user_id"]
    auth_user_id = request.session["_auth_user_id"]
    del request.session["impersonator_user_id"]
    logout(request)

    user = get_user_model().objects.get(pk=impersonator_user_id)
    for backend in settings.AUTHENTICATION_BACKENDS:
        if user == load_backend(backend).get_user(user.pk):
            user.backend = backend
            break

    login(request, user)

    user_url_name = "shuup_admin:user.detail"
    if has_permission(user, user_url_name):
        url = reverse(user_url_name, args=[auth_user_id])
    else:
        url = reverse(settings.SHUUP_ADMIN_LOGIN_AS_STAFF_REDIRECT_VIEW)

    return HttpResponseRedirect(url)
