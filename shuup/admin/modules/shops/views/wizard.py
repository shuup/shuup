# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.shops.forms import (
    ShopAddressWizardForm, ShopWizardForm
)
from shuup.admin.views.wizard import (
    TemplatedWizardFormDef, WizardFormDef, WizardPane
)
from shuup.core.models import TaxClass


class ShopWizardPane(WizardPane):
    identifier = "general"
    icon = "shuup_admin/img/configure.png"
    title = _("Shop Details")
    text = _("Add an address so you can get paid")

    def valid(self):
        from shuup.admin.utils.permissions import has_permission
        return has_permission(self.request.user, "shop.edit")

    def visible(self):
        return not self.object.contact_address

    def get_form_defs(self):
        return [
            TemplatedWizardFormDef(
                name="shop",
                template_name="shuup/admin/shops/_wizard_base_shop_form.jinja",
                extra_js="shuup/admin/shops/_wizard_base_shop_script.jinja",
                form_class=ShopWizardForm,
                kwargs={
                    "instance": self.object,
                    "languages": settings.LANGUAGES
                }
            ),
            WizardFormDef(
                name="address",
                form_class=ShopAddressWizardForm,
                kwargs={
                    "instance": self.object.contact_address,
                    "user": self.request.user
                }
            )
        ]

    def form_valid(self, form):
        form["shop"].save()
        addr = form["address"].save()
        self.object.contact_address = addr
        self.object.save()
        tax_class, created = TaxClass.objects.get_or_create(identifier="default")
        tax_class.name = _("Default Tax Class")
        tax_class.save()
