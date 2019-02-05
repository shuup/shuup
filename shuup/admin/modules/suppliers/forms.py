# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms import ShuupAdminForm
from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.shop_provider import get_shop
from shuup.core.models import MutableAddress, Shop, Supplier


class SupplierBaseForm(ShuupAdminForm):
    class Meta:
        model = Supplier
        exclude = ("module_data", "options", "contact_address")
        widgets = {
            "module_identifier": forms.Select
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(SupplierBaseForm, self).__init__(*args, **kwargs)

        # add shops field when superuser only
        if getattr(self.request.user, "is_superuser", False):
            initial_shops = (self.instance.shops.all() if self.instance.pk else [])
            self.fields["shops"] = Select2MultipleField(
                label=_("Shops"),
                help_text=_("Select shops for this supplier. Keep it blank to share with all shops."),
                model=Shop,
                required=False,
                initial=initial_shops
            )
            self.fields["shops"].choices = initial_shops
            self.fields["shops"].widget.choices = [
                (shop.pk, force_text(shop)) for shop in initial_shops
            ]
        else:
            # drop shops fields
            self.fields.pop("shops", None)

        choices = Supplier.get_module_choices(
            empty_label=(_("No %s module") % Supplier._meta.verbose_name)
        )
        self.fields["module_identifier"].choices = self.fields["module_identifier"].widget.choices = choices

    def clean(self):
        cleaned_data = super(SupplierBaseForm, self).clean()
        stock_managed = cleaned_data.get("stock_managed")
        module_identifier = cleaned_data.get("module_identifier")

        if stock_managed and not module_identifier:
            self.add_error("stock_managed", _("It is not possible to manage inventory when no module is selected."))

        return cleaned_data

    def save(self, commit=True):
        instance = super(SupplierBaseForm, self).save(commit)
        instance.shop_products.remove(
            *list(instance.shop_products.exclude(shop_id__in=instance.shops.all()).values_list("pk", flat=True)))

        if not settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS or "shops" not in self.fields:
            instance.shops.add(get_shop(self.request))

        return instance


class SupplierContactAddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "name", "prefix", "suffix",
            "email", "phone", "tax_number",
            "street", "street2", "street3",
            "postal_code", "city",
            "region_code", "region", "country",
            "latitude", "longitude"
        )
