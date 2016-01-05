# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import time

from django import forms
from django.http.response import HttpResponse, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shoop.addons.reloader import get_reload_method_classes
from shoop.utils.excs import Problem
from shoop.utils.iterables import first


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
            raise Problem("There are no viable reload methods available. Please contact your system administrator.")

        self.fields["reload_method"] = forms.ChoiceField(
            choices=[(rm.identifier, rm.title) for rm in self.reload_methods],
            label=_("Reload Method"),
            initial=self.reload_methods[0].identifier,
            widget=forms.RadioSelect
        )

    def get_selected_reload_method(self):
        return first(rm for rm in self.reload_methods if rm.identifier == self.cleaned_data["reload_method"])


class ReloadView(FormView):
    template_name = "shoop/admin/addons/reload.jinja"
    form_class = ReloadMethodForm

    def form_valid(self, form):
        reloader = form.get_selected_reload_method()
        reloader.execute()
        return HttpResponse("Reloading.")  # This might not reach the user...

    def get(self, request, *args, **kwargs):
        if request.GET.get("ping"):
            return JsonResponse({"pong": time.time()})
        return super(ReloadView, self).get(request, *args, **kwargs)
