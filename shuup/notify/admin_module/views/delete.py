# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.notify.models.script import Script
from shuup.utils.django_compat import reverse


class ScriptDeleteView(DetailView):
    model = Script

    def get_success_url(self):
        return reverse("shuup_admin:notify.script.list")

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        messages.success(request, _("%s has been marked deleted.") % obj)
        return HttpResponseRedirect(self.get_success_url())
