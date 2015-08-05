# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Attribute
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class AttributeForm(MultiLanguageModelForm):
    class Meta:
        model = Attribute
        exclude = ()  # All the fields!


class AttributeEditView(CreateOrUpdateView):
    model = Attribute
    form_class = AttributeForm
    template_name = "shoop/admin/attributes/edit.jinja"
    context_object_name = "attribute"
