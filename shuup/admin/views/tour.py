# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.http.response import JsonResponse
from django.views.generic import View

from shuup import configuration


class TourView(View):
    def post(self, request, *args, **kwargs):
        tour_key = request.POST.get("tourKey", "")
        configuration.set(None, "shuup_%s_tour_complete" % tour_key, True)
        return JsonResponse({"success": True})
