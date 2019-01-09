# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.text import camel_case_to_spaces
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from shuup.admin.toolbar import (
    get_discard_button, JavaScriptActionButton, Toolbar
)
from shuup.admin.utils.urls import get_model_url
from shuup.admin.utils.views import get_create_or_change_title
from shuup.notify.admin_module.forms import ScriptItemEditForm
from shuup.notify.admin_module.utils import get_enum_choices_dict
from shuup.notify.base import Action, Condition, Event
from shuup.notify.enums import StepConditionOperator, StepNext
from shuup.notify.models.script import Script
from shuup.utils.text import snake_case


@csrf_exempt  # This is fine -- the editor itself saves naught
def script_item_editor(request):
    # This is a regular non-CBV view because the way it processes the data it received
    # would be more awkward to do in a CBV.
    request.POST = dict(request.POST.items())  # Make it mutable
    init_data_json = request.POST.pop("init_data")
    init_data = json.loads(init_data_json)
    item_class = {"action": Action, "condition": Condition}[init_data["itemType"]]
    form = ScriptItemEditForm(
        script_item=item_class.unserialize(init_data["data"], validate=False),
        event_class=Event.class_for_identifier(init_data["eventIdentifier"]),
        data=(request.POST if request.POST else None),
        files=(request.FILES if request.FILES else None)
    )
    form.initial = form.get_initial()
    context = {
        "form": form,
        "script_item": form.script_item,
        "event_class": form.event_class,
        "init_data": init_data_json,
    }
    if form.data and form.is_valid():
        try:
            form.save()
        except ValidationError as verr:
            form.add_error(None, verr)
        else:
            context["post_message"] = {"new_data": form.script_item.data}
            # Unbind so we'll use the initial data
            form.is_bound = False
            form.data = {}
            form.initial = form.get_initial()

    return render(request, "notify/admin/script_item_editor.jinja", context)


class ScriptAPI(object):
    def __init__(self, request, script):
        """
        :param request: Request
        :type request: django.http.HttpRequest
        :param script: Script
        :type script: shuup.notify.models.Script
        """
        self.request = request
        self.script = script

    def dispatch(self):
        data = json.loads(self.request.body.decode("UTF-8"))
        command = data.pop("command")
        func_name = "handle_%s" % snake_case(camel_case_to_spaces(command))
        func = getattr(self, func_name, None)
        if not callable(func):
            return JsonResponse({"error": "No handler: %s" % func_name})
        return func(data)

    def handle_get_data(self, data):
        return JsonResponse({
            "steps": self.script.get_serialized_steps(),
        })

    def handle_save_data(self, data):
        try:
            self.script.set_serialized_steps(data["steps"])
        except Exception as exc:
            if settings.DEBUG:
                raise
            return JsonResponse({"error": exc})
        self.script.save(update_fields=("_step_data",))
        return JsonResponse({"success": "Changes saved."})


class EditScriptContentView(DetailView):
    template_name = "notify/admin/script_content_editor.jinja"
    model = Script
    context_object_name = "script"

    def post(self, request, *args, **kwargs):
        return ScriptAPI(request, self.get_object()).dispatch()

    def get_context_data(self, **kwargs):
        context = super(EditScriptContentView, self).get_context_data(**kwargs)
        context["title"] = get_create_or_change_title(self.request, self.object)
        context["action_infos"] = Action.get_ui_info_map()
        context["condition_infos"] = Condition.get_ui_info_map()
        context["cond_op_names"] = get_enum_choices_dict(StepConditionOperator)
        context["step_next_names"] = get_enum_choices_dict(StepNext)
        context["toolbar"] = Toolbar([
            JavaScriptActionButton(
                text=_("Save"), icon="fa fa-save", extra_css_class="btn-success",
                onclick="window.ScriptEditor.save();return false"
            ),
            get_discard_button(get_model_url(self.object, "edit"))
        ], view=self)
        return context
