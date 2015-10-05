# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import MenuEntry
from shoop.admin.forms.fields import PercentageField
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import CustomerTaxGroup, Tax, TaxClass
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class _Breadcrumbed(object):
    def get_breadcrumb_parents(self):
        return [MenuEntry(text=self.parent_name, url=self.parent_url)]


class TaxForm(MultiLanguageModelForm):
    class Meta:
        model = Tax
        fields = ["name", "code", "rate", "amount_value", "currency", "enabled"]

    rate = Tax._meta.get_field("rate").formfield(form_class=PercentageField)


class CustomerTaxGroupForm(MultiLanguageModelForm):
    class Meta:
        model = CustomerTaxGroup
        fields = ["name"]


class TaxClassForm(MultiLanguageModelForm):
    class Meta:
        model = TaxClass
        fields = ["name", "enabled"]


class TaxEditView(_Breadcrumbed, CreateOrUpdateView):
    model = Tax
    form_class = TaxForm
    template_name = "shoop/admin/taxes/edit_tax.jinja"
    context_object_name = "tax"
    add_form_errors_as_messages = True
    parent_name = _("Taxes")
    parent_url = "shoop_admin:tax.list"


class CustomerTaxGroupEditView(_Breadcrumbed, CreateOrUpdateView):
    model = CustomerTaxGroup
    form_class = CustomerTaxGroupForm
    template_name = "shoop/admin/taxes/edit_customer_tax_group.jinja"
    context_object_name = "customer_tax_group"
    parent_name = _("Customer Tax Groups")
    parent_url = "shoop_admin:customer_tax_group.list"


class TaxClassEditView(_Breadcrumbed, CreateOrUpdateView):
    model = TaxClass
    template_name = "shoop/admin/taxes/edit_tax_class.jinja"
    form_class = TaxClassForm
    context_object_name = "tax_class"
    parent_name = _("Tax Classes")
    parent_url = "shoop_admin:tax_class.list"
