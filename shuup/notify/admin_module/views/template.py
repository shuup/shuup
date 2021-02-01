# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from shuup.admin.shop_provider import get_shop
from shuup.apps.provides import get_identifier_to_object_map
from shuup.notify.admin_module import SCRIPT_TEMPLATES_PROVIDE_CATEGORY
from shuup.notify.models import Script


class EditScriptMode(object):
    CREATE = "create"
    MODIFY = "modify"


class ScriptTemplateView(TemplateView):
    template_name = "notify/admin/script_templates.jinja"

    def get_context_data(self, **kwargs):
        """
        Put all the script templates on disposal of the user.
        """
        context = super(ScriptTemplateView, self).get_context_data(**kwargs)
        context["script_templates"] = six.iteritems(get_identifier_to_object_map(SCRIPT_TEMPLATES_PROVIDE_CATEGORY))
        context["edit_mode"] = EditScriptMode.CREATE
        return context

    def post(self, request):
        """
        Create the Script from template directly if the template does not have a bound form.

        If the script template has a bound form, redirect to the template configuration view.

        If no script template is found, redirect to the script list.
        """
        identifier = request.POST.get("id", None)
        script_template_class = get_identifier_to_object_map(SCRIPT_TEMPLATES_PROVIDE_CATEGORY).get(identifier)

        if script_template_class:
            script_template = script_template_class()

            # the template has a form for configuration.. lets redirect to the correct view
            if script_template.get_form():
                return redirect("shuup_admin:notify.script-template-config", id=identifier)
            else:
                shop = get_shop(request)
                script = script_template.create_script(shop)

                if script:
                    script.template = identifier
                    script.save(update_fields=["template"])
                    messages.success(request, _("Script created from template."))

                return redirect("shuup_admin:notify.script.list")
        else:
            messages.error(request, _("Template Script not found."))
            return redirect("shuup_admin:notify.script.list")


class ScriptTemplateConfigView(FormView):
    template_name = "notify/admin/script_template_config.jinja"
    success_url = "shuup_admin:notify.script.list"

    def _get_script_template_class(self):
        """
        Get the script template class from the request kwargs.
        """
        identifier = self.kwargs.get("id", None)
        return get_identifier_to_object_map(SCRIPT_TEMPLATES_PROVIDE_CATEGORY).get(identifier, None)

    def dispatch(self, request, *args, **kwargs):
        """
        Check if the request parameter `id` has a valid script template.
        """
        script_template_class = self._get_script_template_class()
        if not script_template_class:
            messages.error(request, _("Template Script not found."))
            return redirect("shuup_admin:notify.script.list")

        return super(ScriptTemplateConfigView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """
        Create and return the configuration form.
        """
        script_template_class = self._get_script_template_class()
        script_template = script_template_class()
        return script_template.get_form(**self.get_form_kwargs())

    def form_valid(self, form):
        """
        Create the script from the template using the configuration from the form.
        """
        shop = get_shop(self.request)
        script_template = self._get_script_template_class()()
        script = script_template.create_script(shop, form)
        if script:
            script.template = self.kwargs["id"]
            script.save(update_fields=["template"])
            messages.success(self.request, _("Script created from template."))
        return redirect("shuup_admin:notify.script.list")

    def get_context_data(self, **kwargs):
        context = super(ScriptTemplateConfigView, self).get_context_data(**kwargs)
        script_template = self._get_script_template_class()()
        context["script_template"] = script_template
        context["edit_mode"] = EditScriptMode.CREATE
        context.update(script_template.get_context_data())
        return context


class ScriptTemplateEditView(FormView):
    template_name = "notify/admin/script_template_config.jinja"
    success_url = "shuup_admin:notify.script.list"
    instance = None

    def _get_script_template_class(self):
        """
        Get the script template class from script instance.
        """
        return get_identifier_to_object_map(SCRIPT_TEMPLATES_PROVIDE_CATEGORY).get(self.instance.template, None)

    def dispatch(self, request, *args, **kwargs):
        """
        Check if the request parameter `pk` has a valid templated Script instance.
        """
        self.instance = Script.objects.filter(pk=self.kwargs.get("pk")).first()

        if not self.instance or not self.instance.template:
            messages.error(request, _("Templated script not found."))
            return redirect("shuup_admin:notify.script.list")

        return super(ScriptTemplateEditView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """
        Create and return the configuration form.
        """
        script_template_class = self._get_script_template_class()
        script_template = script_template_class(self.instance)
        return script_template.get_form(**self.get_form_kwargs())

    def form_valid(self, form):
        """
        Create the script from the template using the configuration from the form.
        """
        script_template = self._get_script_template_class()(self.instance)
        script_template.update_script(form)
        messages.success(self.request, _("Script updated."))
        return redirect("shuup_admin:notify.script.list")

    def get_context_data(self, **kwargs):
        context = super(ScriptTemplateEditView, self).get_context_data(**kwargs)
        script_template = self._get_script_template_class()(self.instance)
        context["script_template"] = script_template
        context["edit_mode"] = EditScriptMode.MODIFY
        context.update(script_template.get_context_data())
        return context
