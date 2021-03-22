# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.form_modifier import ModifiableFormMixin, ModifiableViewMixin
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Attribute
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class AttributeForm(ModifiableFormMixin, MultiLanguageModelForm):
    form_modifier_provide_key = "admin_extend_attribute_form"

    class Meta:
        model = Attribute
        exclude = ()  # All the fields!


class AttributeEditView(ModifiableViewMixin, CreateOrUpdateView):
    model = Attribute
    form_class = AttributeForm
    template_name = "shuup/admin/attributes/edit.jinja"
    context_object_name = "attribute"

    def get_toolbar(self):
        object = self.get_object()
        delete_url = reverse_lazy("shuup_admin:attribute.delete", kwargs={"pk": object.pk}) if object.pk else None
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)


class AttributeDeleteView(DetailView):
    model = Attribute

    def post(self, request, *args, **kwargs):
        attribute = self.get_object()
        attribute_name = force_text(attribute)
        attribute.delete()
        messages.success(request, _("%s has been deleted.") % attribute_name)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:attribute.list"))
