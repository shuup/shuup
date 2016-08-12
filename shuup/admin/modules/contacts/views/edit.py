# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.transaction import atomic

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.modules.contacts.form_parts import (
    CompanyContactBaseFormPart, PersonContactBaseFormPart
)
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Contact, PersonContact


class ContactEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Contact
    template_name = "shuup/admin/contacts/edit.jinja"
    context_object_name = "contact"
    form_part_class_provide_key = "admin_contact_form_part"

    def get_contact_type(self):
        contact_type = self.request.REQUEST.get("type", "")
        if self.object.pk:
            if type(self.object) is PersonContact:
                contact_type = "person"
            else:
                contact_type = "company"
        return contact_type

    def get_form_part_classes(self):
        form_part_classes = []
        contact_type = self.get_contact_type()
        if contact_type == "person":
            form_part_classes.append(PersonContactBaseFormPart)
        else:
            form_part_classes.append(CompanyContactBaseFormPart)
        form_part_classes += list(get_provide_objects(self.form_part_class_provide_key))
        return form_part_classes

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_toolbar(self):
        toolbar = get_default_edit_toolbar(
            self,
            self.get_save_form_id(),
            discard_url=(get_model_url(self.object) if self.object.pk else None)
        )

        for button in get_provide_objects("admin_contact_edit_toolbar_button"):
            toolbar.append(button(self.object))

        return toolbar

    def get_context_data(self, **kwargs):
        context = super(ContactEditView, self).get_context_data(**kwargs)
        context["contact_type"] = self.get_contact_type()
        return context
