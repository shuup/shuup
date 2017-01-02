# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from enumfields import Enum

from shuup import configuration
from shuup.admin.modules.settings.forms import OrderSettingsForm
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.core.models import ConfigurationItem


class SystemSettingsView(FormView):
    form_class = OrderSettingsForm
    template_name = "shuup/admin/settings/edit.jinja"

    def form_valid(self, form):
        # clear all set configurations
        for key in form.fields.keys():
            try:
                ConfigurationItem.objects.get(shop=None, key=key).delete()
            except ConfigurationItem.DoesNotExist:
                continue

        for key, value in six.iteritems(form.cleaned_data):
            if isinstance(value, Enum):
                value = value.value
            configuration.set(None, key, value)

        messages.success(self.request, _("Saved successfully"))
        return redirect("shuup_admin:settings.list")

    def get_context_data(self, **kwargs):
        context = super(SystemSettingsView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-save",
                form_id="settings_form",
                text=_("Save system settings"),
                extra_css_class="btn-success",
            )
        ])
        return context
