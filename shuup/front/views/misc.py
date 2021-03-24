# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model, load_backend, login, logout
from django.http import HttpResponseForbidden, HttpResponseRedirect

from shuup.core.models import get_company_contact_for_shop_staff
from shuup.core.utils.users import (
    force_anonymous_contact_for_user,
    force_person_contact_for_user,
    toggle_all_seeing_for_user,
)
from shuup.front.utils.user import is_admin_user
from shuup.utils.django_compat import reverse


def toggle_all_seeing(request):
    return_url = request.META["HTTP_REFERER"]
    if not is_admin_user(request):
        return HttpResponseRedirect(return_url)

    toggle_all_seeing_for_user(request.user)
    return HttpResponseRedirect(return_url)


def force_anonymous_contact(request):
    return_url = request.META["HTTP_REFERER"]
    if not is_admin_user(request):
        return HttpResponseRedirect(return_url)

    user = request.user
    force_anonymous_contact_for_user(user, True)
    force_person_contact_for_user(user, False)
    return HttpResponseRedirect(return_url)


def force_person_contact(request):
    return_url = request.META["HTTP_REFERER"]
    if not is_admin_user(request):
        return HttpResponseRedirect(return_url)

    user = request.user
    force_person_contact_for_user(user, True)
    force_anonymous_contact_for_user(user, False)
    return HttpResponseRedirect(return_url)


def force_company_contact(request):
    return_url = request.META["HTTP_REFERER"]
    if not is_admin_user(request):
        return HttpResponseRedirect(return_url)

    user = request.user
    force_anonymous_contact_for_user(user, False)
    force_person_contact_for_user(user, False)

    get_company_contact_for_shop_staff(request.shop, user)
    return HttpResponseRedirect(return_url)


def stop_impersonating(request):
    if "impersonator_user_id" not in request.session:
        return HttpResponseForbidden()

    impersonator_user_id = request.session["impersonator_user_id"]
    auth_user_id = request.session["_auth_user_id"]
    del request.session["impersonator_user_id"]
    logout(request)

    user = get_user_model().objects.get(pk=impersonator_user_id)
    for backend in django_settings.AUTHENTICATION_BACKENDS:
        if user == load_backend(backend).get_user(user.pk):
            user.backend = backend
            break

    login(request, user)
    return HttpResponseRedirect(reverse("shuup_admin:user.detail", args=[auth_user_id]))
