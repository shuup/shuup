# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.modules.contacts.form_parts import (
    CompanyContactBaseFormPart, ContactAddressesFormPart,
    PersonContactBaseFormPart
)
from shuup.admin.modules.contacts.utils import (
    check_contact_permission, request_limited
)
from shuup.admin.shop_provider import get_shop
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

    def get_object(self, queryset=None):
        if not self.kwargs.get(self.pk_url_kwarg):
            return self.model()
        contact = super(CreateOrUpdateView, self).get_object(queryset)
        check_contact_permission(self.request, contact)
        return contact

    def get_contact_type(self):
        contact_type = self.request.GET.get("type", "")
        if self.object.pk:
            if type(self.object) is PersonContact:
                contact_type = "person"
            else:
                contact_type = "company"
        return contact_type

    def get_queryset(self):
        qs = super(ContactEditView, self).get_queryset()

        if request_limited(self.request):
            qs = qs.filter(shops=get_shop(self.request))

        # non superusers can't see superusers contacts
        if not self.request.user.is_superuser:
            qs = qs.exclude(PersonContact___user__is_superuser=True)

        return qs

    def get_form_part_classes(self):
        form_part_classes = []
        contact_type = self.get_contact_type()
        if contact_type == "person":
            form_part_classes.append(PersonContactBaseFormPart)
        else:
            form_part_classes.append(CompanyContactBaseFormPart)
        form_part_classes += list(get_provide_objects(self.form_part_class_provide_key))
        if self.object.pk:
            form_part_classes.append(ContactAddressesFormPart)
        return form_part_classes

    @atomic
    def form_valid(self, form):
        response = self.save_form_parts(form)
        self.object.add_to_shop(get_shop(self.request))
        return response

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
        contact_type = self.get_contact_type()
        context["contact_type"] = contact_type
        if not self.object.pk:
            context["title"] = _("New Company") if contact_type == "company" else _("New Contact")
        return context
