# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Attribute, ProductType
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class ProductTypeForm(MultiLanguageModelForm):
    attributes = Select2MultipleField(model=Attribute, required=False, help_text=_(
        "Select attributes that go with your product type. These are defined in Products Settings - Attributes."
    ))

    class Meta:
        model = ProductType
        exclude = ()

    def __init__(self, **kwargs):
        super(ProductTypeForm, self).__init__(**kwargs)
        if self.instance.pk:
            choices = [(a.pk, a.name) for a in self.instance.attributes.all()]
            self.fields["attributes"].initial = [pk for pk, name in choices]

    def clean_attributes(self):
        attributes = [int(a_id) for a_id in self.cleaned_data.get("attributes", [])]
        return Attribute.objects.filter(pk__in=attributes).all()

    def save(self, commit=True):
        obj = super(ProductTypeForm, self).save(commit=commit)
        obj.attributes.clear()
        obj.attributes = self.cleaned_data["attributes"]
        return self.instance


class ProductTypeEditView(CreateOrUpdateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = "shuup/admin/product_types/edit.jinja"
    context_object_name = "product_type"
