# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db.models import Q
from django.db.transaction import atomic

from shuup.admin.form_part import (
    FormPart, FormPartsViewMixin, SaveFormPartsMixin, TemplatedFormDef
)
from shuup.admin.modules.suppliers.forms import (
    SupplierBaseForm, SupplierContactAddressForm
)
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.views import (
    check_and_raise_if_only_one_allowed, CreateOrUpdateView
)
from shuup.core.models import Supplier


class SupplierBaseFormPart(FormPart):
    priority = 1

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            SupplierBaseForm,
            template_name="shuup/admin/suppliers/_edit_base_form.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "request": self.request,
                "languages": settings.LANGUAGES,

            }
        )

    def form_valid(self, form):
        self.object = form["base"].save()


class SupplierContactAddressFormPart(FormPart):
    priority = 2

    def get_form_defs(self):
        initial = {}
        yield TemplatedFormDef(
            "address",
            SupplierContactAddressForm,
            template_name="shuup/admin/suppliers/_edit_contact_address_form.jinja",
            required=False,
            kwargs={
                "instance": self.object.contact_address,
                "initial": initial
            }
        )

    def form_valid(self, form):
        addr_form = form["address"]
        if addr_form.changed_data:
            addr = addr_form.save()
            setattr(self.object, "contact_address", addr)
            self.object.save()


class SupplierEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Supplier
    template_name = "shuup/admin/suppliers/edit.jinja"
    context_object_name = "supplier"
    base_form_part_classes = [SupplierBaseFormPart, SupplierContactAddressFormPart]
    form_part_class_provide_key = "admin_supplier_form_part"

    def get_object(self, queryset=None):
        obj = super(SupplierEditView, self).get_object(queryset)
        check_and_raise_if_only_one_allowed("SHUUP_ENABLE_MULTIPLE_SUPPLIERS", obj)
        return obj

    def get_queryset(self):
        if getattr(self.request.user, "is_superuser", False):
            return Supplier.objects.all()
        return Supplier.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True))

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)
