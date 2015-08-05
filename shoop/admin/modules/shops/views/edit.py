# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals
from django.forms.models import modelform_factory
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Shop
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class ShopEditView(CreateOrUpdateView):
    model = Shop
    form_class = modelform_factory(Shop, MultiLanguageModelForm, exclude=("owner", "options"))
    template_name = "shoop/admin/shops/edit.jinja"
    context_object_name = "shop"
