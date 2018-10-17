# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.contrib import messages
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import JavaScriptActionButton, Toolbar
from shuup.core.models import Category


class CategoryOrganizeView(TemplateView):
    template_name = "shuup/admin/categories/organize.jinja"

    def get_context_data(self):
        shop = get_shop(self.request)
        context = super(CategoryOrganizeView, self).get_context_data()
        context["categories"] = Category.objects.all_except_deleted(shop=shop).filter(
            parent__isnull=True
        )
        context["toolbar"] = self.get_toolbar()
        context["title"] = _("Organize categories")
        context["customer"] = self.request.customer
        return context

    def get_toolbar(self):
        toolbar = Toolbar.for_view(self)
        toolbar.append(
            JavaScriptActionButton(
                onclick="window.saveCategories();",
                text=_("Save"),
                icon="fa fa-save",
                extra_css_class="btn-success"
            )
        )
        return toolbar

    def handle_category_node(self, node, parent_id=None):
        update_attrs = {}

        if "position" in node:
            update_attrs["ordering"] = node["position"]
        if "visible_in_menu" in node:
            update_attrs["visible_in_menu"] = bool(node["visible_in_menu"])

        Category.objects.filter(pk=node["id"]).update(
            parent_id=parent_id,
            **update_attrs
        )
        for child in node.get("children", []):
            self.handle_category_node(child, node["id"])

    def post(self, request):
        payload = request.POST.get("payload")

        if payload:
            data = json.loads(payload)

            with atomic():
                for node in data:
                    self.handle_category_node(node)
            Category.objects.rebuild()
            messages.success(request, _("Categories saved"))
        else:
            messages.error(request, _("Payload is missing from the request"))

        return self.get(request)
