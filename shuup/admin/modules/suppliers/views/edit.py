# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from django.db.transaction import atomic

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import (
    check_and_raise_if_only_one_allowed, CreateOrUpdateView
)
from shuup.core.models import Supplier
from shuup.utils.django_compat import reverse


class SupplierEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Supplier
    template_name = "shuup/admin/suppliers/edit.jinja"
    context_object_name = "supplier"
    base_form_part_classes = []
    form_part_class_provide_key = "admin_supplier_form_part"

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        delete_url = None
        supplier = self.get_object()
        if supplier and supplier.pk:
            delete_url = reverse("shuup_admin:supplier.delete", kwargs={"pk": supplier.pk})
        return get_default_edit_toolbar(self, save_form_id, delete_url=delete_url)

    def get_object(self, queryset=None):
        obj = super(SupplierEditView, self).get_object(queryset)
        check_and_raise_if_only_one_allowed("SHUUP_ENABLE_MULTIPLE_SUPPLIERS", obj)
        return obj

    def get_queryset(self):
        if getattr(self.request.user, "is_superuser", False):
            return Supplier.objects.not_deleted()
        return Supplier.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True)).not_deleted()

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)
