# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponseRedirect

from shuup.core.models import get_company_contact_for_shop_staff
from shuup.core.utils.users import (
    force_anonymous_contact_for_user, force_person_contact_for_user,
    toggle_all_seeing_for_user
)
from shuup.front.utils.user import is_admin_user


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
