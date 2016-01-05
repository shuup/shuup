# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import ContactGroup
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class ContactGroupForm(MultiLanguageModelForm):
    class Meta:
        model = ContactGroup
        fields = ("name",)


class ContactGroupEditView(CreateOrUpdateView):
    model = ContactGroup
    form_class = ContactGroupForm
    template_name = "shoop/admin/contact_groups/edit.jinja"
    context_object_name = "contact_group"
