# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from enumfields import Enum

from shuup.admin.module_registry import get_modules
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.utils.tour import is_tour_complete
from shuup.admin.utils.wizard import (
    load_setup_wizard_panes, setup_wizard_complete
)


class HelpBlockCategory(Enum):
    PRODUCTS = 1
    ORDERS = 2
    CAMPAIGNS = 3
    CONTACTS = 4
    STOREFRONT = 5

    GENERAL = 200

    class Labels:
        PRODUCTS = _("Products")
        CONTACTS = _("Contacts")
        STOREFRONT = _("Storefront")
        CAMPAIGNS = _("Campaigns")
        ORDERS = _("Orders")
        GENERAL = _("General")


QUICKLINK_ORDER = [
    HelpBlockCategory.PRODUCTS,
    HelpBlockCategory.ORDERS,
    HelpBlockCategory.CAMPAIGNS,
    HelpBlockCategory.CONTACTS,
    HelpBlockCategory.STOREFRONT,
    HelpBlockCategory.GENERAL
]


class SimpleHelpBlock(object):
    def __init__(self, text, **kwargs):
        self.text = text
        self.description = kwargs.pop("description", "")
        self.actions = kwargs.pop("actions", [])
        self.icon_url = kwargs.pop("icon_url", None)
        self.priority = kwargs.pop("priority", 1)
        self.css_class = kwargs.pop("css_class", "")
        self.done = kwargs.pop("done", False)
        self.required = kwargs.pop("required", True)
        self.category = kwargs.pop("category", HelpBlockCategory.GENERAL)


class HomeView(TemplateView):
    template_name = "shuup/admin/home/home.jinja"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context["blocks"] = blocks = []
        context["tour_key"] = "home"
        context["tour_complete"] = is_tour_complete(get_shop(self.request), "home")
        wizard_complete = setup_wizard_complete(self.request)

        wizard_url = reverse("shuup_admin:wizard")
        wizard_actions = []
        if not wizard_complete:
            wizard_actions.append({
                "text": _("Complete wizard"),
                "url": wizard_url
            })
        else:
            wizard_steps = load_setup_wizard_panes(
                shop=self.request.shop, request=self.request, visible_only=False)
            for step in wizard_steps:
                wizard_actions.append({
                    "text": step.title,
                    "url": "%s?pane_id=%s" % (wizard_url, step.identifier),
                    "no_redirect": True
                })

        blocks.append(
            SimpleHelpBlock(
                _("Complete the setup wizard"),
                actions=wizard_actions,
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
                css_class="green ",
                actions=[{
                    "method": "POST",
                    "text": _("Publish shop"),
                    "url": reverse("shuup_admin:shop.enable", kwargs={"pk": self.request.shop.pk}),
                    "data": {
                        "enable": True,
                        "redirect": reverse("shuup_admin:dashboard")
                    }
                }],
                icon_url="shuup_admin/img/publish.png",
                done=not self.request.shop.maintenance_mode
            )
        )
        return context
