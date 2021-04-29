# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Attribute


class AttributeEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Attribute
    template_name = "shuup/admin/attributes/edit.jinja"
    context_object_name = "attribute"
    base_form_part_classes = []
    form_part_class_provide_key = "admin_attribute_form_part"
    add_form_errors_as_messages = True

    def get_toolbar(self):
        object = self.get_object()
        delete_url = reverse_lazy("shuup_admin:attribute.delete", kwargs={"pk": object.pk}) if object.pk else None
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)


class AttributeDeleteView(DetailView):
    model = Attribute

    def post(self, request, *args, **kwargs):
        attribute = self.get_object()
        attribute_name = force_text(attribute)
        attribute.delete()
        messages.success(request, _("%s has been deleted.") % attribute_name)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:attribute.list"))
