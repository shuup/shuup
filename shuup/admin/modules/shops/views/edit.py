# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import View

from shuup.admin.form_part import (
    FormPart, FormPartsViewMixin, SaveFormPartsMixin, TemplatedFormDef
)
from shuup.admin.modules.shops.forms import ContactAddressForm, ShopBaseForm
from shuup.admin.shop_provider import set_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import (
    check_and_raise_if_only_one_allowed, CreateOrUpdateView
)
from shuup.admin.utils.wizard import onboarding_complete
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Shop
from shuup.core.settings_provider import ShuupSettings
from shuup.utils.django_compat import reverse


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
                "languages": settings.LANGUAGES
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


class ShopEnablerView(View):
    def post(self, request, *args, **kwargs):
        if not onboarding_complete(request):
            messages.error(request, _("There are still some pending actions to complete."))
            return HttpResponseRedirect(reverse("shuup_admin:home"))
        enable = request.POST.get("enable", True)
        if kwargs.get("pk") == str(request.shop.pk):
            shop = request.shop
        else:
            shop = Shop.objects.filter(pk=kwargs.get("pk")).first()
        shop.maintenance_mode = not enable
        shop.save()
        messages.info(request, _("Your store is now live."))
        return HttpResponseRedirect(request.POST.get("redirect"))


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
        with_split_save = ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS")
        toolbar = get_default_edit_toolbar(
            self, save_form_id, with_split_save=with_split_save)

        for button in get_provide_objects("admin_shop_edit_toolbar_button"):
            if button.visible_for_object(self.object):
                toolbar.append(button(self.object))

        return toolbar

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_queryset(self):
        return Shop.objects.get_for_user(self.request.user)


class ShopSelectView(View):
    def get(self, request, *args, **kwargs):
        shop = Shop.objects.filter(pk=kwargs.get("pk")).first()
        set_shop(request, shop)
        messages.info(request, (_("Shop {} is now active.")).format(shop.name))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse("shuup_admin:home")))
