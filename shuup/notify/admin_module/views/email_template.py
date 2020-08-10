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

from shuup.admin.forms import ShuupAdminFormNoTranslation
from shuup.admin.forms.widgets import CodeEditorWidget
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.picotable import Column
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.notify.models import EmailTemplate
from shuup.utils.django_compat import reverse_lazy


class EmailTemplateForm(ShuupAdminFormNoTranslation):
    class Meta:
        model = EmailTemplate
        fields = ("name", "template")
        widgets = {
            "template": CodeEditorWidget()
        }


class EmailTemplateEditView(CreateOrUpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "notify/admin/email_template_edit.jinja"
    context_object_name = "email_template"

    def get_toolbar(self):
        object = self.get_object()
        delete_url = (
            reverse_lazy("shuup_admin:notify.email_template.delete", kwargs={"pk": object.pk})
            if object.pk else None
        )
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)


class EmailTemplateDeleteView(DetailView):
    model = EmailTemplate

    def post(self, request, *args, **kwargs):
        email_template = self.get_object()
        email_template_name = email_template.name
        email_template.delete()
        messages.success(request, _("%s has been deleted.") % email_template_name)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:notify.email_template.list"))


class EmailTemplateListView(PicotableListView):
    model = EmailTemplate
    default_columns = [
        Column(
            "name",
            _("Name"),
        )
    ]
    toolbar_buttons_provider_key = "email_template_list_toolbar_provider"
    mass_actions_provider_key = "email_template_list_mass_actions_provider"
