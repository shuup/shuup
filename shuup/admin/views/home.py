# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.utils.wizard import setup_wizard_complete


class SimpleHelpBlock(object):
    def __init__(self, text, **kwargs):
        self.text = text
        self.description = kwargs.pop("description", "")
        self.actions = kwargs.pop("actions", [])
        self.icon_url = kwargs.pop("icon_url", None)
        self.priority = kwargs.pop("priority", 1)
        self.css_class = kwargs.pop("css_class", "")
        self.done = kwargs.pop("done", False)


class HomeView(TemplateView):
    template_name = "shuup/admin/home/home.jinja"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context["blocks"] = blocks = []
        wizard_complete = setup_wizard_complete()
        blocks.append(
            SimpleHelpBlock(
                _("Complete the setup wizard"),
                actions=[{
                    "text": _("Complete wizard"),
                    "url": reverse("shuup_admin:wizard")
                }] if not wizard_complete else [],
                icon_url="shuup_admin/img/configure.png",
                priority=-1,
                done=wizard_complete
            )
        )

        for module in get_modules():
            if not get_missing_permissions(self.request.user, module.get_required_permissions()):
                blocks.extend(module.get_help_blocks(request=self.request, kind="setup"))
        blocks.sort(key=lambda b: b.priority)
        blocks.append(
            SimpleHelpBlock(
                priority=1000,
                text=_("Publish your store"),
                description=_("Let customers browse your store and make purchases"),
                css_class="green",
                actions=[{
                    "method": "POST",
                    "text": _("Publish shop"),
                    "url": reverse("shuup_admin:shop.enable", kwargs={"pk": self.request.shop.pk}),
                    "data": {
                        "enable": True,
                        "redirect": reverse("shuup_admin:dashboard")
                    }
                }],
                icon_url="shuup_admin/img/publish.png"
            )
        )
        return context
