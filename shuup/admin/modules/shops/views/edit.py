# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db.transaction import atomic

from shuup import configuration
from shuup.admin.form_part import (
    FormPart, FormPartsViewMixin, SaveFormPartsMixin, TemplatedFormDef
)
from shuup.admin.modules.shops.forms import ContactAddressForm, ShopBaseForm
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import (
    check_and_raise_if_only_one_allowed, CreateOrUpdateView
)
from shuup.core.models import Shop


class ShopBaseFormPart(FormPart):
    priority = 1

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            ShopBaseForm,
            template_name="shuup/admin/shops/_edit_base_shop_form.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "languages": configuration.get(self.object, "languages", settings.LANGUAGES)
            }
        )

    def form_valid(self, form):
        self.object = form["base"].save()


class ContactAddressFormPart(FormPart):
    priority = 2

    def get_form_defs(self):
        initial = {}
        yield TemplatedFormDef(
            "address",
            ContactAddressForm,
            template_name="shuup/admin/shops/_edit_contact_address_form.jinja",
            required=False,
            kwargs={"instance": self.object.contact_address, "initial": initial}
        )

    def form_valid(self, form):
        addr_form = form["address"]
        if addr_form.changed_data:
            addr = addr_form.save()
            setattr(self.object, "contact_address", addr)
            self.object.save()


class ShopEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Shop
    template_name = "shuup/admin/shops/edit.jinja"
    context_object_name = "shop"
    base_form_part_classes = [ShopBaseFormPart, ContactAddressFormPart]
    form_part_class_provide_key = "admin_shop_form_part"

    def get_object(self, queryset=None):
        obj = super(ShopEditView, self).get_object(queryset)
        check_and_raise_if_only_one_allowed("SHUUP_ENABLE_MULTIPLE_SHOPS", obj)

        return obj

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        return get_default_edit_toolbar(self, save_form_id, with_split_save=settings.SHUUP_ENABLE_MULTIPLE_SHOPS)

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)
