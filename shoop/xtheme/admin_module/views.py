# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.apps.provides import get_provide_objects
from shoop.xtheme.models import ThemeSettings
from shoop.xtheme.theme import get_current_theme, set_current_theme, get_theme_by_identifier


class ActivationForm(forms.Form):
    """
    A very simple form for activating a theme.
    """
    activate = forms.CharField()


class ThemeConfigView(FormView):
    """
    A view for listing and activating themes.
    """
    template_name = "shoop/xtheme/admin/config.jinja"
    form_class = ActivationForm

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigView, self).get_context_data(**kwargs)
        context["theme_classes"] = sorted(
            [t for t in get_provide_objects("xtheme") if t.identifier],
            key=lambda t: (t.name or t.identifier)
        )
        context["current_theme"] = get_current_theme()
        return context

    def form_valid(self, form):
        identifier = form.cleaned_data["activate"]
        set_current_theme(identifier)
        messages.success(self.request, _("Theme activated."))
        return HttpResponseRedirect(self.request.path)


class ThemeConfigDetailView(CreateOrUpdateView):
    """
    A view for configuring a single theme.
    """
    model = ThemeSettings
    template_name = "shoop/xtheme/admin/config_detail.jinja"
    form_class = forms.Form
    context_object_name = "theme_settings"
    add_form_errors_as_messages = True

    def get_object(self, queryset=None):
        ts, _ = ThemeSettings.objects.get_or_create(theme_identifier=self.kwargs["theme_identifier"])
        return ts

    def get_theme(self):
        """
        Get the theme object to configure.

        :return: Theme object
        :rtype: shoop.xtheme.theme.Theme
        """
        return get_theme_by_identifier(
            identifier=self.kwargs["theme_identifier"],
            settings_obj=self.object
        )

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigDetailView, self).get_context_data(**kwargs)
        context["theme"] = self.get_theme()
        return context

    def get_form(self, form_class=None):
        return self.get_theme().get_configuration_form(form_kwargs=self.get_form_kwargs())

    def get_success_url(self):
        return reverse("shoop_admin:xtheme.config_detail", kwargs={
            "theme_identifier": self.object.theme_identifier
        })
