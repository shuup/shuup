# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.encoding import force_text
from django.views.generic import DetailView
from shuup.admin.form_modifier import ModifiableFormMixin, ModifiableViewMixin
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


class AttributeDeleteView(DetailView):
    model = Attribute

    def post(self, request, *args, **kwargs):
        attribute = self.get_object()
        attribute_name = force_text(attribute)
        attribute.delete()
        messages.success(request, _("%s has been deleted.") % attribute_name)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:attribute.list"))
