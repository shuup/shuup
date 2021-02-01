# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.breadcrumbs import BreadcrumbedView
from shuup.admin.forms.fields import PercentageField
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import CustomerTaxGroup, Tax, TaxClass
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


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


class TaxEditView(BreadcrumbedView, CreateOrUpdateView):
    model = Tax
    form_class = TaxForm
    template_name = "shuup/admin/taxes/edit_tax.jinja"
    context_object_name = "tax"
    add_form_errors_as_messages = True
    parent_name = _("Taxes")
    parent_url = "shuup_admin:tax.list"


class CustomerTaxGroupEditView(BreadcrumbedView, CreateOrUpdateView):
    model = CustomerTaxGroup
    form_class = CustomerTaxGroupForm
    template_name = "shuup/admin/taxes/edit_customer_tax_group.jinja"
    context_object_name = "customer_tax_group"
    parent_name = _("Customer Tax Groups")
    parent_url = "shuup_admin:customer_tax_group.list"


class TaxClassEditView(BreadcrumbedView, CreateOrUpdateView):
    model = TaxClass
    template_name = "shuup/admin/taxes/edit_tax_class.jinja"
    form_class = TaxClassForm
    context_object_name = "tax_class"
    parent_name = _("Tax Classes")
    parent_url = "shuup_admin:tax_class.list"
