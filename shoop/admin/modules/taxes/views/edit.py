# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.admin.forms.fields import PercentageField
from shoop.admin.utils.forms import add_form_errors_as_messages
from shoop.admin.utils.views import CreateOrUpdateView, add_create_or_change_message
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

    def form_valid(self, form):
        add_create_or_change_message(self.request, self.object, is_new=(not self.object.pk))
        return super(TaxEditView, self).form_valid(form)

    def form_invalid(self, form):
        add_form_errors_as_messages(self.request, form)
        return super(TaxEditView, self).form_invalid(form)


class CustomerTaxGroupEditView(CreateOrUpdateView):
    model = CustomerTaxGroup
    form_class = CustomerTaxGroupForm
    template_name = "shoop/admin/taxes/edit_customer_tax_group.jinja"
    context_object_name = "customer_tax_group"

    def form_valid(self, form):
        add_create_or_change_message(self.request, self.object, is_new=(not self.object.pk))
        return super(CustomerTaxGroupEditView, self).form_valid(form)


class TaxClassEditView(CreateOrUpdateView):
    model = TaxClass
    template_name = "shoop/admin/taxes/edit_tax_class.jinja"
    form_class = TaxClassForm
    context_object_name = "tax_class"

    def form_valid(self, form):
        add_create_or_change_message(self.request, self.object, is_new=(not self.object.pk))
        return super(TaxClassEditView, self).form_valid(form)
