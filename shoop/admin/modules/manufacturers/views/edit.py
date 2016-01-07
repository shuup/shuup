# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.forms.models import ModelForm

from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Manufacturer


class ManufacturerForm(ModelForm):
    class Meta:
        model = Manufacturer
        exclude = ("identifier", "created_on")


class ManufacturerEditView(CreateOrUpdateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "shoop/admin/manufacturers/edit.jinja"
    context_object_name = "manufacturer"
