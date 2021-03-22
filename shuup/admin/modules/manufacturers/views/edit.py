# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.forms import ShuupAdminFormNoTranslation
from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Manufacturer, Shop
from shuup.utils.django_compat import force_text, reverse_lazy


class ManufacturerForm(ShuupAdminFormNoTranslation):
    class Meta:
        model = Manufacturer
        fields = ("name", "shops", "url", "logo")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ManufacturerForm, self).__init__(*args, **kwargs)
        # add shops field when superuser only
        if getattr(self.request.user, "is_superuser", False):
            self.fields["shops"] = Select2MultipleField(
                label=_("Shops"),
                help_text=_("Select shops for this manufacturer. Keep it blank to share with all shops."),
                model=Shop,
                required=False,
            )
            initial_shops = self.instance.shops.all() if self.instance.pk else []
            self.fields["shops"].widget.choices = [(shop.pk, force_text(shop)) for shop in initial_shops]
        else:
            # drop shops fields
            self.fields.pop("shops", None)

    def save(self, commit=True):
        is_superuser = getattr(self.request.user, "is_superuser", False)

        # do not let any user to change shared Manufacturers
        if self.instance.pk and self.instance.shops.count() == 0 and not is_superuser:
            raise forms.ValidationError(_("You have no permission to change a shared Manufacturer."))

        instance = super(ManufacturerForm, self).save(commit)

        # if shops field is not available and it is a new manufacturer, set the current shop
        if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS or "shops" not in self.fields:
            instance.shops.add(get_shop(self.request))

        return instance


class ManufacturerEditView(CreateOrUpdateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "shuup/admin/manufacturers/edit.jinja"
    context_object_name = "manufacturer"

    def get_queryset(self):
        return Manufacturer.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True))

    def get_form_kwargs(self):
        kwargs = super(ManufacturerEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_toolbar(self):
        object = self.get_object()
        delete_url = reverse_lazy("shuup_admin:manufacturer.delete", kwargs={"pk": object.pk}) if object.pk else None
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["front_url"] == "/None":
            context["front_url"] = None

        return context


class ManufacturerDeleteView(DetailView):
    model = Manufacturer

    def get_queryset(self):
        return Manufacturer.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True))

    def post(self, request, *args, **kwargs):
        manufacturer = self.get_object()
        manufacturer_name = force_text(manufacturer)
        manufacturer.delete()
        messages.success(request, _("%s has been deleted.") % manufacturer_name)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:manufacturer.list"))
