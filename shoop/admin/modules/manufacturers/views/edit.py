# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.forms.models import ModelForm
from django.utils.translation import ugettext as _

from shoop.admin.toolbar import URLActionButton
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

    def get_toolbar(self):
        toolbar = super(ManufacturerEditView, self).get_toolbar()
        if self.object.pk:
            toolbar.append(
                URLActionButton(
                    text=_("Create Purchase Order"),
                    icon="fa fa-plus",
                    url=reverse("shoop_admin:purchase_order.new") + "?manufacturer_id=%s" % self.object.pk,
                    tooltip=_(u"Create an order for the manufacturer."),
                    extra_css_class="btn-success"
                )
            )
        return toolbar
