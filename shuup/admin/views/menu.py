# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import JsonResponse
from django.views.generic import TemplateView, View


class MenuView(TemplateView):
    template_name = "shuup/admin/base/_main_menu.jinja"


class MenuToggleView(View):
    def post(self, request, *args, **kwargs):
        request.session["menu_open"] = not bool(request.session.get("menu_open", True))
        return JsonResponse({"success": True})
