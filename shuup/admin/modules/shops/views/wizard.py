# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.modules.shops.forms import (
    ShopAddressWizardForm, ShopLanguagesWizardForm, ShopWizardForm
)
from shuup.admin.views.wizard import (
    TemplatedWizardFormDef, WizardFormDef, WizardPane
)
from shuup.core.models import TaxClass


class ShopLanguagesWizardPane(WizardPane):
    identifier = "languages"
    text = _("Please select the languages supported by your shop")

    def visible(self):
        return not configuration.get(self.object, "languages", None)

    def get_form_defs(self):
        return [
            WizardFormDef(
                name="shop_languages",
                extra_js="shuup/admin/shops/_change_languages_script.jinja",
                form_class=ShopLanguagesWizardForm,
                kwargs={
                    "initial": {
                        "languages": configuration.get(self.object, "languages", [settings.LANGUAGE_CODE])
                    }
                }
            )
        ]

    def form_valid(self, form):
        languages = form["shop_languages"].cleaned_data.get("languages")
        shop_languages = [(code, name) for code, name in settings.LANGUAGES if code in languages]
        configuration.set(self.object, "languages", shop_languages)


class ShopWizardPane(WizardPane):
    identifier = "general"
    icon = "shuup_admin/img/configure.png"
    text = _("Please enter your shop details")

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
                    "languages": configuration.get(self.object, "languages", settings.LANGUAGES)
                }
            ),
            WizardFormDef(
                name="address",
                form_class=ShopAddressWizardForm,
                kwargs={
                    "instance": self.object.contact_address
                }
            )
        ]

    def form_valid(self, form):
        form["shop"].save()
        addr_form = form["address"]
        if addr_form.changed_data:
            addr = addr_form.save()
            self.object.contact_address = addr
            self.object.save()
        tax_class, created = TaxClass.objects.get_or_create(identifier="default")
        tax_class.name = _("Default Tax Class")
        tax_class.save()
