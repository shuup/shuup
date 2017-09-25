# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.campaigns.admin_module.forms import (
    BasketCampaignForm, CatalogCampaignForm
)

from .form_sets import (
    BasketConditionsFormSet, BasketDiscountEffectsFormSet,
    BasketLineEffectsFormSet, CatalogConditionsFormSet, CatalogEffectsFormSet,
    CatalogFiltersFormSet
)


class CampaignBaseFormPart(FormPart):
    priority = -1000  # Show this first
    form = None  # Override in subclass

    def __init__(self, *args, **kwargs):
        super(CampaignBaseFormPart, self).__init__(*args, **kwargs)

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            self.form,
            required=True,
            template_name="shuup/campaigns/admin/_edit_base_form.jinja",
            kwargs={"instance": self.object, "languages": settings.LANGUAGES, "request": self.request}
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object


class CatalogBaseFormPart(CampaignBaseFormPart):
    form = CatalogCampaignForm


class BasketBaseFormPart(CampaignBaseFormPart):
    form = BasketCampaignForm


class BaseFormPart(FormPart):
    formset = None
    template_name = "shuup/campaigns/admin/_edit_form.jinja"

    def __init__(self, request, form, name, owner):
        self.name = name
        self.form = form
        super(BaseFormPart, self).__init__(request, object=owner)

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.formset,
            self.template_name,
            required=False,
            kwargs={"form": self.form, "owner": self.object},
        )

    def form_valid(self, form):
        component_form = form.forms[self.name]
        component_form.save()

        for component in component_form.new_objects:
            if self.name.startswith("conditions"):
                self.object.conditions.add(component)
            elif self.name.startswith("filters"):
                self.object.filters.add(component)


class BasketConditionsFormPart(BaseFormPart):
    formset = BasketConditionsFormSet


class BasketDiscountEffectsFormPart(BaseFormPart):
    formset = BasketDiscountEffectsFormSet


class BasketLineEffectsFormPart(BaseFormPart):
    formset = BasketLineEffectsFormSet


class CatalogConditionsFormPart(BaseFormPart):
    formset = CatalogConditionsFormSet


class CatalogFiltersFormPart(BaseFormPart):
    formset = CatalogFiltersFormSet


class CatalogEffectsFormPart(BaseFormPart):
    formset = CatalogEffectsFormSet
