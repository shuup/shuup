# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import time

from django import forms
from django.conf import settings
from django.core.management import call_command
from django.http.response import HttpResponse, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from six import StringIO

from shuup.addons.manager import get_enabled_addons
from shuup.addons.reloader import get_reload_method_classes
from shuup.apps.settings import reload_apps
from shuup.utils.excs import Problem
from shuup.utils.iterables import first


class ReloadMethodForm(forms.Form):
    def get_viable_reload_methods(self):
        for klass in get_reload_method_classes():
            rm = klass()
            if rm.is_viable():
                yield rm

    def __init__(self, **kwargs):
        super(ReloadMethodForm, self).__init__(**kwargs)
        self.reload_methods = list(self.get_viable_reload_methods())

        if not self.reload_methods:
            raise Problem(_("There are no viable reload methods available. Please contact your system administrator."))

        self.fields["reload_method"] = forms.ChoiceField(
            choices=[(rm.identifier, rm.title) for rm in self.reload_methods],
            label=_("Reload Method"),
            initial=self.reload_methods[0].identifier,
            widget=forms.RadioSelect
        )

    def get_selected_reload_method(self):
        return first(rm for rm in self.reload_methods if rm.identifier == self.cleaned_data["reload_method"])


def finalize_installation_for_enabled_apps():
    out = StringIO()
    enabled_addons = get_enabled_addons(settings.SHUUP_ENABLED_ADDONS_FILE)
    new_apps = [app for app in enabled_addons if app not in settings.INSTALLED_APPS]
    if new_apps:
        out.write("Enabling new addons: %s" % new_apps)
        settings.INSTALLED_APPS += type(settings.INSTALLED_APPS)(new_apps)
        reload_apps()

    call_command("migrate", "--noinput", "--no-color", stdout=out)
    call_command("collectstatic", "--noinput", "--no-color", stdout=out)
    return out.getvalue()


class ReloadView(FormView):
    template_name = "shuup/admin/addons/reload.jinja"
    form_class = ReloadMethodForm

    def form_valid(self, form):
        reloader = form.get_selected_reload_method()
        reloader.execute()
        return HttpResponse(_("Reloading."))  # This might not reach the user...

    def get(self, request, *args, **kwargs):
        if request.GET.get("ping"):
            return JsonResponse({"pong": time.time()})
        elif request.GET.get("finalize"):
            return JsonResponse({"message": finalize_installation_for_enabled_apps()})
        return super(ReloadView, self).get(request, *args, **kwargs)
