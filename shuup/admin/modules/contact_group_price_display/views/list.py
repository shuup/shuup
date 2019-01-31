# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.contact_group_price_display.views.forms import (
    get_price_display_mode, PriceDisplayChoices
)
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import Column
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import (
    ContactGroupPriceDisplay, get_groups_for_price_display_create,
    get_price_displays_for_shop
)


class ContactGroupPriceDisplayListView(PicotableListView):
    model = ContactGroupPriceDisplay
    default_columns = [
        Column("group", _(u"Group"), display="group"),
        Column("display_mode", _(u"Display Mode"), display="show_display_mode")
    ]
    toolbar_buttons_provider_key = "contact_group_price_list_toolbar_provider"
    mass_actions_provider_key = "contact_group_price_list_mass_actions_provider"

    def get_queryset(self):
        if getattr(self.request.user, "is_superuser", False):
            ContactGroupPriceDisplay.objects.all()
        shop = get_shop(self.request)
        return get_price_displays_for_shop(shop)

    def show_display_mode(self, instance):
        display_mode = get_price_display_mode(self.request, instance)
        for k, v in PriceDisplayChoices.choices():
            if k == display_mode:
                return force_text(v).title()
        return _("Unspecified")

    def get_context_data(self, **kwargs):
        context = super(ContactGroupPriceDisplayListView, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            settings_button = SettingsActionButton.for_model(
                ContactGroupPriceDisplay, return_url="contact_group_price_display")
        else:
            settings_button = None

        shop = get_shop(self.request)
        can_create = len(get_groups_for_price_display_create(shop))
        context["toolbar"] = Toolbar([
            NewActionButton("shuup_admin:contact_group_price_display.new") if can_create else None,
            settings_button
        ], view=self)
        return context
