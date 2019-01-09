# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import Toolbar, URLActionButton
from shuup.admin.utils.views import (
    add_create_or_change_message, CreateOrUpdateView
)
from shuup.apps.provides import get_identifier_to_object_map
from shuup.notify.admin_module import SCRIPT_TEMPLATES_PROVIDE_CATEGORY
from shuup.notify.admin_module.forms import ScriptForm
from shuup.notify.models.script import Script


class ScriptEditView(CreateOrUpdateView):
    model = Script
    form_class = ScriptForm
    template_name = "notify/admin/edit_script.jinja"
    context_object_name = "script"

    def get_context_data(self, **kwargs):
        context = super(ScriptEditView, self).get_context_data(**kwargs)
        if self.object.pk:
            buttons = []

            edit_button_title = _("Edit Script Contents")

            # this script was created through a template
            # so show an option to easily edit the template
            if self.object.template:
                template_cls = get_identifier_to_object_map(SCRIPT_TEMPLATES_PROVIDE_CATEGORY).get(self.object.template)

                # check whether is possible to edit the script through the template editor
                if template_cls and template_cls(self.object).can_edit_script():
                    # change the editor button title to advanced mode
                    edit_button_title = _("Edit Script (advanced)")

                    buttons.append(
                        URLActionButton(
                            text=_("Edit Template"),
                            icon="fa fa-pencil-square-o",
                            extra_css_class="btn-primary",
                            url=reverse("shuup_admin:notify.script-template-edit", kwargs={"pk": self.object.pk})
                        )
                    )

            buttons.insert(0, URLActionButton(
                text=edit_button_title,
                icon="fa fa-pencil",
                extra_css_class="btn-primary",
                url=reverse("shuup_admin:notify.script.edit-content", kwargs={"pk": self.object.pk})
            ))
            context["toolbar"] = Toolbar(buttons, view=self)
        return context

    def get_form_kwargs(self):
        kwargs = super(ScriptEditView, self).get_form_kwargs()
        kwargs["shop"] = get_shop(self.request)
        return kwargs

    def form_valid(self, form):
        is_new = (not self.object.pk)
        wf = form.save()
        if is_new:
            return redirect("shuup_admin:notify.script.edit-content", pk=wf.pk)
        else:
            add_create_or_change_message(self.request, self.object, is_new=is_new)
            return redirect("shuup_admin:notify.script.edit", pk=wf.pk)

    def get_queryset(self):
        return super(ScriptEditView, self).get_queryset().filter(shop=get_shop(self.request))
