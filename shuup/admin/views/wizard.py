# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.http.response import HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.utils.wizard import (
    load_setup_wizard_pane, load_setup_wizard_panes
)
from shuup.core.models import Shop
from shuup.utils.form_group import FormDef, FormGroup
from shuup.utils.iterables import first


class WizardFormDefMixin(object):
    def __init__(self, **kwargs):
        self.context = kwargs.pop("context", {})
        self.extra_js = kwargs.pop("extra_js", "")
        super(WizardFormDefMixin, self).__init__(**kwargs)


class WizardFormDef(WizardFormDefMixin, FormDef):
    pass


class TemplatedWizardFormDef(WizardFormDefMixin, TemplatedFormDef):
    pass


class _WizardFormGroup(FormGroup):
    def __init__(self, identifier, title, text, icon, can_skip, **kwargs):
        super(_WizardFormGroup, self).__init__(**kwargs)
        self.identifier = identifier
        self.title = title
        self.text = text
        self.icon = icon
        self.can_skip = can_skip


class WizardPane(FormPart):
    identifier = None
    title = None
    text = None
    icon = None
    can_skip = False
    editable = True

    def visible(self):
        """
        Returns whether this pane is visible for editing.
        """
        return True

    def valid(self):
        """
        Returns whether this pane is valid and should be included in wizard pane list.
        """
        return True


class WizardView(TemplateView):
    template_name = "shuup/admin/wizard/wizard.jinja"

    @cached_property
    def panes(self):
        shop = self.request.shop
        pane_id = self.request.GET.get("pane_id", None)
        panes = load_setup_wizard_panes(
            shop=shop,
            request=self.request,
            # if the user presses "previous" then "next" again, resubmit the form
            visible_only=self.request.method == "GET"
        )
        if not panes and pane_id:
            pane = load_setup_wizard_pane(
                shop=shop,
                request=self.request,
                pane_id=pane_id
            )
            if pane:
                panes.append(pane)
        return panes

    def get_all_pane_forms(self):
        return [self.get_form_group_for_pane(pane) for pane in self.panes]

    @cached_property
    def current_pane(self):
        pane_id = self.request.POST.get("pane_id")
        return first(filter(lambda x: x.identifier == pane_id, self.panes), None)

    def get_final_pane_identifier(self):
        visible_panes = list(filter(lambda x: x.visible(), self.panes))
        if len(visible_panes) > 0:
            return visible_panes[-1].identifier
        return 0

    def get_context_data(self, **kwargs):
        context = super(WizardView, self).get_context_data(**kwargs)
        context["panes"] = self.get_all_pane_forms()
        context["active_pane_id"] = self.request.GET.get("pane_id", 1)
        context["final_pane_id"] = self.get_final_pane_identifier()
        return context

    def get_form_group_for_pane(self, pane):
        kwargs = {}
        if self.request.method == "POST":
            kwargs.update({
                "data": self.request.POST,
                "files": self.request.FILES
            })
        fg = _WizardFormGroup(pane.identifier, pane.title, pane.text, pane.icon, pane.can_skip, **kwargs)
        for form_def in pane.get_form_defs():
            fg.form_defs[form_def.name] = form_def
        return fg

    def get_form(self):
        return self.get_form_group_for_pane(self.current_pane)

    def form_valid(self, form):
        pane = self.current_pane
        pane.form_valid(form)
        return JsonResponse({"success": "true"}, status=200)

    def form_invalid(self, form):
        return JsonResponse(form.errors, status=400)

    @atomic
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        abort = request.POST.get("abort", False)
        if self.request.POST.get("pane_id") == self.get_final_pane_identifier():
            configuration.set(Shop.objects.first(), "setup_wizard_complete", True)
        if abort:
            return JsonResponse({"success": "true"}, status=200)
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @atomic
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if len(self.panes) == 0:
            if request.shop.maintenance_mode:
                return HttpResponseRedirect(reverse("shuup_admin:home"))
            else:
                return HttpResponseRedirect(reverse("shuup_admin:dashboard"))
        return super(WizardView, self).get(request, *args, **kwargs)
