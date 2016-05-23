# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.apps import apps
from django.db.models import Q
from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from shoop.core.models import Contact, Product


class MultiselectAjaxView(TemplateView):
    model = None
    search_fields = []
    result_limit = 20

    def init_search_fields(self, cls):
        self.search_fields = []
        key = "%sname" % ("translations__" if hasattr(cls, "translations") else "")
        self.search_fields.append(key)
        if issubclass(cls, Contact):
            self.search_fields.append("email")
        if isinstance(cls, Product):
            self.search_fields.append("sku")

    def get_data(self, request, *args, **kwargs):
        model_name = request.GET.get("model")
        if not model_name:
            return []
        cls = apps.get_model(model_name)
        self.init_search_fields(cls)
        if not self.search_fields:
            return [{"id": None, "name": _("Couldn't get selections for %s.") % model_name}]
        if request.GET.get("search"):
            query = Q()
            keyword = request.GET.get("search")
            for field in self.search_fields:
                query |= Q(**{"%s__icontains" % field: keyword})
            objects = cls.objects.filter(query).distinct()
        else:
            objects = cls.objects.all()
        return [{"id": obj.id, "name": force_text(obj)} for obj in objects[:self.result_limit]]

    def get(self, request, *args, **kwargs):
        return JsonResponse({"results": self.get_data(request, *args, **kwargs)})
