# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.addons.manager import get_addons_from_entry_points, get_enabled_addons, set_enabled_addons
from shuup.admin.toolbar import NewActionButton, PostActionButton, Toolbar, URLActionButton
from shuup.utils.django_compat import reverse
from shuup.utils.http import get_client_ip


class AddonEnableDisableForm(forms.Form):
    def __init__(self, **kwargs):
        super(AddonEnableDisableForm, self).__init__(**kwargs)
        self.addons = sorted(get_addons_from_entry_points())
        self._create_fields()

    def _create_fields(self):
        enabled_addons = get_enabled_addons(settings.SHUUP_ENABLED_ADDONS_FILE)
        for addon in sorted(self.addons):
            self.fields[addon] = forms.BooleanField(
                required=False, initial=(addon in enabled_addons), label=_("Enable %s") % addon
            )

    def get_enabled_addons(self):
        return [addon for addon in self.addons if self.cleaned_data.get(addon)]


class AddonListView(FormView):
    template_name = "shuup/admin/addons/list.jinja"
    form_class = AddonEnableDisableForm

    def form_valid(self, form):
        old_enabled_addons = get_enabled_addons(settings.SHUUP_ENABLED_ADDONS_FILE)
        new_enabled_addons = form.get_enabled_addons()
        changes = []
        n_add = len(set(new_enabled_addons) - set(old_enabled_addons))
        n_del = len(set(old_enabled_addons) - set(new_enabled_addons))
        if n_add:
            changes.append(_("%d new addons enabled.") % n_add)
        if n_del:
            changes.append(_("%d previously enabled addons disabled.") % n_del)
        if changes:
            set_enabled_addons(
                settings.SHUUP_ENABLED_ADDONS_FILE,
                new_enabled_addons,
                comment="Written via Shuup admin (user %s; IP %s; time %s)"
                % (self.request.user.pk, get_client_ip(self.request), now().isoformat()),
            )
            messages.success(self.request, " ".join(changes))
            return HttpResponseRedirect(self.request.path + "?reload=1")

        messages.info(self.request, _("No changes were made."))
        return HttpResponseRedirect(self.request.path)

    def get_context_data(self, **kwargs):
        context = super(AddonListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar(
            [
                PostActionButton(
                    icon="fa fa-save",
                    form_id="addon_list",
                    text=_("Save addon changes"),
                    extra_css_class="btn-success",
                ),
                NewActionButton(
                    reverse("shuup_admin:addon.upload"),
                    text=_("Upload new addon"),
                    extra_css_class="btn-info",
                    icon="fa fa-upload",
                ),
            ],
            view=self,
        )
        if self.request.GET.get("reload"):
            context["toolbar"].append(
                URLActionButton(
                    reverse("shuup_admin:addon.reload"),
                    text=_("Reload application"),
                    extra_css_class="btn-warning",
                    icon="fa fa-refresh",
                )
            )

        return context
