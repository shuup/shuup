# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView

from shuup import configuration
from shuup.admin.menu import (
    CUSTOM_ADMIN_MENU_STAFF_KEY, CUSTOM_ADMIN_MENU_SUPERUSER_KEY,
    CUSTOM_ADMIN_MENU_SUPPLIER_KEY, CUSTOM_ADMIN_MENU_USER_PREFIX,
    get_menu_entry_categories
)
from shuup.utils.django_compat import reverse_lazy


class AdminMenuArrangeView(TemplateView):
    """
    Retrieve menus from configuration or display default
    """
    template_name = "shuup/admin/menu/arrange.jinja"
    success_url = reverse_lazy('shuup_admin:menu.arrange_supplier')
    reset_url = reverse_lazy('shuup_admin:menu.reset')

    def get_context_data(self, **kwargs):
        """
        Populate context with admin_menus
        """
        context = super(AdminMenuArrangeView, self).get_context_data(**kwargs)
        context["admin_menus"] = get_menu_entry_categories(self.request)
        context["reset_url"] = self.reset_url
        return context

    def set_configuration(self, request, menus):
        configuration.set(
            None, CUSTOM_ADMIN_MENU_USER_PREFIX.format(request.user.pk), menus
        )

    def post(self, request):
        """
        Save admin menu for current user to the database
        """
        self.set_configuration(request, json.loads(request.POST.get('menus')))
        messages.add_message(request, messages.SUCCESS, _('Menu saved'))
        return HttpResponseRedirect(self.success_url)


class AdminMenuResetView(RedirectView):
    """
    Reset admin menu to default values
    """
    permanent = False
    url = reverse_lazy('shuup_admin:menu.arrange')

    def reset_configuration(self, request):
        configuration.set(
            None, CUSTOM_ADMIN_MENU_USER_PREFIX.format(request.user.pk), None
        )

    def get(self, request, *args, **kwargs):
        self.reset_configuration(request)
        messages.add_message(request, messages.SUCCESS, _('Menu reset'))
        return super(AdminMenuResetView, self).get(request, *args, **kwargs)


class SuperUserMenuArrangeView(AdminMenuArrangeView):
    success_url = reverse_lazy('shuup_admin:menu.arrange_superuser')
    reset_url = reverse_lazy('shuup_admin:menu.reset_superuser')

    def set_configuration(self, request, menus):
        configuration_object = configuration.get(
            None, CUSTOM_ADMIN_MENU_SUPERUSER_KEY, {}
        ) or {}
        configuration_object.update({
            get_language(): menus
        })
        configuration.set(None, CUSTOM_ADMIN_MENU_SUPERUSER_KEY, configuration_object)


class SuperUserMenuResetView(AdminMenuResetView):
    url = reverse_lazy('shuup_admin:menu.arrange_superuser')

    def reset_configuration(self, request):
        configuration.set(None, CUSTOM_ADMIN_MENU_SUPERUSER_KEY, None)


class StaffMenuArrangeView(AdminMenuArrangeView):
    success_url = reverse_lazy('shuup_admin:menu.arrange_staff')
    reset_url = reverse_lazy('shuup_admin:menu.reset_staff')

    def set_configuration(self, request, menus):
        configuration_object = configuration.get(
            None, CUSTOM_ADMIN_MENU_STAFF_KEY, {}
        ) or {}
        configuration_object.update({
            get_language(): menus
        })
        configuration.set(None, CUSTOM_ADMIN_MENU_STAFF_KEY, configuration_object)


class StaffMenuResetView(AdminMenuResetView):
    url = reverse_lazy('shuup_admin:menu.arrange_staff')

    def reset_configuration(self, request):
        configuration.set(None, CUSTOM_ADMIN_MENU_STAFF_KEY, None)


class SupplierMenuArrangeView(AdminMenuArrangeView):
    success_url = reverse_lazy('shuup_admin:menu.arrange_supplier')
    reset_url = reverse_lazy('shuup_admin:menu.reset_supplier')

    def set_configuration(self, request, menus):
        configuration_object = configuration.get(
            None, CUSTOM_ADMIN_MENU_SUPPLIER_KEY, {}
        ) or {}
        configuration_object.update({
            get_language(): menus
        })
        configuration.set(None, CUSTOM_ADMIN_MENU_SUPPLIER_KEY, configuration_object)


class SupplierMenuResetView(AdminMenuResetView):
    url = reverse_lazy('shuup_admin:menu.arrange_supplier')

    def reset_configuration(self, request):
        configuration.set(None, CUSTOM_ADMIN_MENU_SUPPLIER_KEY, None)
