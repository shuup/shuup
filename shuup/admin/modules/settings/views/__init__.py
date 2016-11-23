# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib import messages
from django.core.urlresolvers import resolve, reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.admin.modules.settings import ViewSettings
from shuup.admin.modules.settings.forms import ColumnSettingsForm
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.utils.importing import load


class ListSettingsView(FormView):
    form_class = ColumnSettingsForm
    template_name = "shuup/admin/edit_settings.jinja"

    def dispatch(self, request, *args, **kwargs):
        module_str = "%s:%s" % (request.GET.get("module"), request.GET.get("model"))
        self.return_url = reverse("shuup_admin:%s.list" % request.GET.get("return_url"))
        match = resolve(self.return_url)
        default_columns = load("%s:%s" % (match.func.__module__, match.func.__name__)).default_columns
        self.model = load(module_str)
        self.settings = ViewSettings(self.model, default_columns)
        return super(ListSettingsView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        return ColumnSettingsForm(self.settings, **kwargs)

    def get_initial(self):
        initial = super(ListSettingsView, self).get_initial()
        for col in self.settings.columns:
            key = self.settings.get_settings_key(col.id)
            initial.update({
                key: self.settings.get_config(col.id)
            })
        return initial

    def form_valid(self, form):
        for col, val in six.iteritems(form.cleaned_data):
            self.settings.set_config(col, val, use_key=True)
        messages.success(self.request, _("Settings saved"), fail_silently=True)
        return HttpResponseRedirect(self.return_url)

    def get_context_data(self, **kwargs):
        context = super(ListSettingsView, self).get_context_data(**kwargs)
        context["toolbar"] = get_default_edit_toolbar(self, "settings_form", with_split_save=False)
        return context
