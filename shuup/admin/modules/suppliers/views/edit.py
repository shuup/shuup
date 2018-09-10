# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.views import (
    check_and_raise_if_only_one_allowed, CreateOrUpdateView
)
from shuup.core.models import Shop, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        exclude = ("module_data",)
        widgets = {
            "module_identifier": forms.Select
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(SupplierForm, self).__init__(*args, **kwargs)

        # add shops field when superuser only
        if getattr(self.request.user, "is_superuser", False):
            self.fields["shops"] = Select2MultipleField(
                label=_("Shops"),
                help_text=_("Select shops for this supplier. Keep it blank to share with all shops."),
                model=Shop,
                required=False
            )
            initial_shops = (self.instance.shops.all() if self.instance.pk else [])
            self.fields["shops"].widget.choices = [(shop.pk, force_text(shop)) for shop in initial_shops]
        else:
            # drop shops fields
            self.fields.pop("shops", None)

    def clean(self):
        cleaned_data = super(SupplierForm, self).clean()
        stock_managed = cleaned_data.get("stock_managed")
        module_identifier = cleaned_data.get("module_identifier")

        if stock_managed and not module_identifier:
            self.add_error("stock_managed", _("It is not possible to manage inventory when no module is selected."))

        return cleaned_data

    def save(self, commit=True):
        instance = super(SupplierForm, self).save(commit)
        instance.shop_products.remove(
            *list(instance.shop_products.exclude(shop_id__in=instance.shops.all()).values_list("pk", flat=True)))

        if not settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS or "shops" not in self.fields:
            instance.shops.add(get_shop(self.request))

        return instance


class SupplierEditView(CreateOrUpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "shuup/admin/suppliers/edit.jinja"
    context_object_name = "supplier"

    def get_object(self, queryset=None):
        obj = super(SupplierEditView, self).get_object(queryset)
        check_and_raise_if_only_one_allowed("SHUUP_ENABLE_MULTIPLE_SUPPLIERS", obj)
        return obj

    def get_queryset(self):
        if getattr(self.request.user, "is_superuser", False):
            return Supplier.objects.all()

        return Supplier.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True))

    def get_form(self, form_class=None):
        form = super(SupplierEditView, self).get_form(form_class=form_class)
        choices = self.model.get_module_choices(
            empty_label=(_("No %s module") % self.model._meta.verbose_name)
        )
        form.fields["module_identifier"].choices = form.fields["module_identifier"].widget.choices = choices
        return form

    def get_form_kwargs(self):
        kwargs = super(SupplierEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
