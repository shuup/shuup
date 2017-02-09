# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponseRedirect
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Shop
from shuup.utils.excs import Problem


def set_shop(request):
    next = request.POST.get("next", request.GET.get("next"))
    if not is_safe_url(url=next, host=request.get_host()):
        next = request.META.get("HTTP_REFERER")
        if not is_safe_url(url=next, host=request.get_host()):
            next = "/"
    user = request.user
    is_superuser = getattr(user, "is_superuser", False)
    if request.method == "POST":
        shop_id = int(request.POST.get("shop", request.GET.get("shop")))
        if not (is_superuser or Shop.objects.filter(id=shop_id, staff_members__id=user.id).exists()):
            raise Problem(_("User %(current_user)s don't have permission to view shop" % {"current_user": user}))
        request.session["admin_shop"] = Shop.objects.get(id=shop_id)
    return HttpResponseRedirect(next)
