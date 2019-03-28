# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.breadcrumbs import BreadcrumbedView
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.core.models import OrderStatus, OrderStatusManager, OrderStatusRole
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class OrderStatusForm(MultiLanguageModelForm):

    class Meta:
        model = OrderStatus
        exclude = ["default"]

    def __init__(self, **kwargs):
        super(OrderStatusForm, self).__init__(**kwargs)
        if self.instance.pk and OrderStatusManager().is_default(self.instance):
            del self.fields['identifier']
            del self.fields['role']
            del self.fields['ordering']
            del self.fields['is_active']

    def clean(self):
        if self.instance.pk and OrderStatusManager().is_default(self.instance):
            data = self.cleaned_data
            data["identifier"] = self.instance.identifier
            return data

        qs = OrderStatus.objects.filter(identifier=self.cleaned_data["identifier"])
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            self.add_error("identifier", _("Identifier already exists"))

        return super(OrderStatusForm, self).clean()

    def save(self, commit=True):
        self.instance.identifier = self.cleaned_data["identifier"]
        return super(OrderStatusForm, self).save(commit)


class OrderStatusEditView(BreadcrumbedView, CreateOrUpdateView):
    model = OrderStatus
    form_class = OrderStatusForm
    template_name = "shuup/admin/orders/status.jinja"
    context_object_name = "status"
    parent_name = _("Order Statuses")
    parent_url = "shuup_admin:order_status.list"


class OrderStatusListView(PicotableListView):
    model = OrderStatus
    default_columns = [
        Column("identifier", _("Identifier"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column(
            "name",
            _("Name"),
            linked=True,
            filter_config=TextFilter(
                operator="startswith",
                filter_field="translations__name"
            )
        ),
        Column(
            "public_name",
            _("Public Name"),
            linked=False,
            filter_config=TextFilter(
                operator="startswith",
                filter_field="translations__name"
            )
        ),
        Column("role", _("Role"), linked=False, filter_config=ChoicesFilter(choices=OrderStatusRole.choices)),
        Column(
            "default", _("Default"), linked=False, filter_config=ChoicesFilter([(False, _("yes")), (True, _("no"))])),
        Column(
            "is_active", _("Active"), linked=False, filter_config=ChoicesFilter([(False, _("yes")), (True, _("no"))])),
    ]
