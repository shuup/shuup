# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import RedirectView, TemplateView

from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.menu import get_menu_entry_categories


class AdminMenuArrangeView(TemplateView):
    """
    Retrieve menus from configuration or display default
    """
    template_name = "shuup/admin/menu/arrange.jinja"

    def get_context_data(self, **kwargs):
        """
        Populate context with admin_menus
        """
        context = super(AdminMenuArrangeView, self).get_context_data(**kwargs)
        context["admin_menus"] = get_menu_entry_categories(self.request)
        return context

    def post(self, request):
        """
        Save admin menu for current user to the database
        """
        menus = json.loads(request.POST.get('menus'))
        configuration.set(None, 'admin_menu_user_{}'.format(request.user.pk), menus)
        messages.add_message(request, messages.SUCCESS, _('Menu saved'))
        return HttpResponseRedirect(reverse_lazy('shuup_admin:menu.arrange'))


class AdminMenuResetView(RedirectView):
    """
    Reset admin menu to default values
    """
    permanent = False
    url = reverse_lazy('shuup_admin:menu.arrange')

    def get(self, request, *args, **kwargs):
        configuration.set(None, 'admin_menu_user_{}'.format(request.user.pk), None)
        messages.add_message(request, messages.SUCCESS, _('Menu reset'))
        return super(AdminMenuResetView, self).get(request, *args, **kwargs)
