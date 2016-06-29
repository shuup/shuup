# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.forms.models import ModelForm

from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Manufacturer


class ManufacturerForm(ModelForm):
    class Meta:
        model = Manufacturer
        exclude = ("identifier", "created_on")


class ManufacturerEditView(CreateOrUpdateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "shuup/admin/manufacturers/edit.jinja"
    context_object_name = "manufacturer"
