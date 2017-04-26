# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.forms import BaseModelFormSet
from django.utils.translation import ugettext_lazy as _

from shuup.campaigns.models import (
    BasketCondition, BasketDiscountEffect, BasketLineEffect, CatalogFilter,
    ContextCondition, ProductDiscountEffect
)
from shuup.campaigns.models.basket_line_effects import FreeProductLine
from shuup.core.models import ShopProduct
from shuup.utils.multilanguage_model_form import TranslatableModelForm


class BaseFormset(BaseModelFormSet):
    form_class = None  # Set in initialization
    model = None  # Override this in subclass

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 20
    absolute_max = 20
    can_delete = True
    can_order = False
    extra = 0

    def __init__(self, *args, **kwargs):
        self.form_class = kwargs.pop("form")
        self.owner = kwargs.pop("owner")
        kwargs.pop("empty_permitted")
        super(BaseFormset, self).__init__(*args, **kwargs)

    def get_name(self):
        return getattr(self._get_actual_model(), "name", None)

    def _get_actual_model(self):
        return self.form_class._meta.model

    def get_queryset(self):
        raise NotImplemented("Override this in subclass")

    def form(self, **kwargs):
        if issubclass(self.form_class, TranslatableModelForm):
            kwargs.setdefault("languages", settings.LANGUAGES)
            kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return self.form_class(**kwargs)


class BasketConditionsFormSet(BaseFormset):
    model = BasketCondition

    def get_queryset(self):
        return self.owner.conditions.instance_of(self._get_actual_model())


class EffectsFormset(BaseFormset):
    def form(self, **kwargs):
        kwargs.setdefault("initial", {"campaign": self.owner})
        return super(EffectsFormset, self).form(**kwargs)


class BasketDiscountEffectsFormSet(EffectsFormset):
    model = BasketDiscountEffect

    def get_queryset(self):
        return self.owner.discount_effects.instance_of(self._get_actual_model())


class BasketLineEffectsFormSet(EffectsFormset):
    model = BasketLineEffect

    def get_queryset(self):
        return self.owner.line_effects.instance_of(self._get_actual_model())

    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        # Apply cleaning if model is FreeProductLine
        if self._get_actual_model() == FreeProductLine:
            for form in self.forms:
                products_ids = form.cleaned_data["products"]
                quantity = form.cleaned_data["quantity"]
                for product_id in products_ids:
                    shop_product = ShopProduct.objects.get(product_id=product_id)
                    step = shop_product.quantity_step
                    if quantity % step != 0:
                        n = (quantity // step)
                        smaller_qty = max(1, n) * step
                        larger_qty = (n + 1) * step
                        form.add_error("quantity",
                                       _("Quantity doesn't match with product units. "
                                         "Closest quantities that match are {smaller_qty} and {larger_qty}")
                                       .format(smaller_qty=smaller_qty, larger_qty=larger_qty))


class CatalogConditionsFormSet(BaseFormset):
    model = ContextCondition

    def get_queryset(self):
        return self.owner.conditions.instance_of(self._get_actual_model())


class CatalogFiltersFormSet(BaseFormset):
    model = CatalogFilter

    def get_queryset(self):
        return self.owner.filters.instance_of(self._get_actual_model())


class CatalogEffectsFormSet(EffectsFormset):
    model = ProductDiscountEffect

    def get_queryset(self):
        return self.owner.effects.instance_of(self._get_actual_model())
