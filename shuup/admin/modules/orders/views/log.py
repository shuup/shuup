# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.http.response import Http404, JsonResponse
from django.views.generic import View

from shuup.core.models import Order, OrderLogEntry, Shop
from shuup.utils.analog import LogEntryKind
from shuup.utils.django_compat import force_text
from shuup.utils.i18n import get_locally_formatted_datetime


class NewLogEntryView(View):
    """
    Create a log `note` item associated with a particular order.
    """
    def post(self, request, *args, **kwargs):
        shop_ids = Shop.objects.get_for_user(self.request.user).values_list("id", flat=True)
        order = Order.objects.filter(pk=kwargs["pk"], shop_id__in=shop_ids).first()
        if not order:
            raise Http404()

        message = request.POST["message"]
        entry = OrderLogEntry.objects.create(
            target=order,
            message=message,
            kind=LogEntryKind.NOTE,
            user=request.user,
        )

        return JsonResponse({
            "message": entry.message,
            "kind": force_text(entry.kind.label),
            "created_on": get_locally_formatted_datetime(entry.created_on),
            "user": force_text(getattr(entry.user, get_user_model().USERNAME_FIELD)),
        })
