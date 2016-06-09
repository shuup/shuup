# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Attribute
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class AttributeForm(MultiLanguageModelForm):
    class Meta:
        model = Attribute
        exclude = ()  # All the fields!


class AttributeEditView(CreateOrUpdateView):
    model = Attribute
    form_class = AttributeForm
    template_name = "shuup/admin/attributes/edit.jinja"
    context_object_name = "attribute"
