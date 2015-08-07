# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.admin.forms.fields import PercentageField
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Tax, CustomerTaxGroup, TaxClass
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class TaxForm(MultiLanguageModelForm):
    class Meta:
        model = Tax
        fields = ["name", "rate", "amount", "enabled"]

    rate = Tax._meta.get_field("rate").formfield(form_class=PercentageField)


class CustomerTaxGroupForm(MultiLanguageModelForm):
    class Meta:
        model = CustomerTaxGroup
        fields = ["name"]


class TaxClassForm(MultiLanguageModelForm):
    class Meta:
        model = TaxClass
        fields = ["name", "enabled"]


class TaxEditView(CreateOrUpdateView):
    model = Tax
    form_class = TaxForm
    template_name = "shoop/admin/taxes/edit_tax.jinja"
    context_object_name = "tax"
    add_form_errors_as_messages = True


class CustomerTaxGroupEditView(CreateOrUpdateView):
    model = CustomerTaxGroup
    form_class = CustomerTaxGroupForm
    template_name = "shoop/admin/taxes/edit_customer_tax_group.jinja"
    context_object_name = "customer_tax_group"


class TaxClassEditView(CreateOrUpdateView):
    model = TaxClass
    template_name = "shoop/admin/taxes/edit_tax_class.jinja"
    form_class = TaxClassForm
    context_object_name = "tax_class"
