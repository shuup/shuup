# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.forms import ShuupAdminForm
from shuup.core.models import WeightBasedPriceRange, WeightBasedPricingBehaviorComponent


class WeightBasedPriceRangeForm(ShuupAdminForm):
    class Meta:
        model = WeightBasedPriceRange
        exclude = []

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("languages", settings.LANGUAGES)
        kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        super(WeightBasedPriceRangeForm, self).__init__(**kwargs)


class CustomRangeFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(CustomRangeFormSet, self).__init__(*args, **kwargs)

    def get_name(self):
        return _("Weight-based pricing range")


class WeightBasedPricingFormPart(FormPart):
    name = "weight_based_price_ranges"
    formset = forms.inlineformset_factory(
        WeightBasedPricingBehaviorComponent,
        WeightBasedPriceRange,
        form=WeightBasedPriceRangeForm,
        formset=CustomRangeFormSet,
        fk_name="component",
        extra=0,
        max_num=20,
        min_num=0,
        validate_max=False,
        validate_min=False,
    )

    def __init__(self, request, object):
        self.component = object.behavior_components.instance_of(WeightBasedPricingBehaviorComponent).first()
        if not self.component:
            self.component = WeightBasedPricingBehaviorComponent()
        super(WeightBasedPricingFormPart, self).__init__(request, object)

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.formset,
            "shuup/admin/services/_edit_weight_based_pricing_form.jinja",
            required=False,
            kwargs={"instance": self.component},
        )

    def form_valid(self, form):
        ranges_formset = form.forms[self.name]
        # Save the instance first
        ranges_formset.instance.save()
        ranges = ranges_formset.save()
        if ranges:  # Make sure that component is linked to service
            self.object.behavior_components.add(ranges_formset.instance)
