# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytz
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from django.views import View


class SetTimezoneView(View):
    """
    This view can be called to set the current user's timezone.
    """

    def post(self, request):
        tz_name = request.POST.get("tz_name")

        try:
            pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            return HttpResponseBadRequest(_("Invalid timezone"))

        request.session["tz"] = tz_name

        if hasattr(request, "person") and request.person and str(request.person.timezone) != tz_name:
            request.person.timezone = tz_name
            request.person.save(update_fields=["timezone"])

        return HttpResponse()
