# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.db.transaction import atomic

from shoop.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import ContactGroup

from .forms import ContactGroupBaseFormPart, ContactGroupMembersFormPart


class ContactGroupEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = ContactGroup
    template_name = "shoop/admin/contact_groups/edit.jinja"
    context_object_name = "contact_group"
    base_form_part_classes = [ContactGroupBaseFormPart, ContactGroupMembersFormPart]

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)
