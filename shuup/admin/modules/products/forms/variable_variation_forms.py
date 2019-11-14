# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import random

import six
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.transaction import atomic
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.forms.widgets import ProductChoiceWidget
from shuup.admin.shop_provider import get_shop
from shuup.core.excs import ImpossibleProductModeException, Problem
from shuup.core.models import (
    Product, ProductVariationVariable, ProductVariationVariableValue
)
from shuup.utils.i18n import get_language_name
from shuup.utils.multilanguage_model_form import to_language_codes


class VariableVariationChildrenForm(forms.Form):
    def __init__(self, **kwargs):
        self.parent_product = kwargs.pop("parent_product")
        self.request = kwargs.pop("request", None)
        super(VariableVariationChildrenForm, self).__init__(**kwargs)
        self._build_fields()

    def _build_fields(self):
        for combo in self.parent_product.get_all_available_combinations():
            field = forms.ModelChoiceField(
                queryset=Product.objects.all(),
                # TODO: Add a mode for ProductChoiceWidget to only allow eligible variation children to be selected
                widget=ProductChoiceWidget(clearable=True),
                required=False,
                initial=combo["result_product_pk"],
                label=_("variable combination")
            )
            field.combo = combo
            self.fields["r_%s" % combo["hash"]] = field

    def _save_combo(self, combo):
        """
        :param combo: Combo description dict, from `get_all_available_combinations`.
        :type combo: dict
        """
        new_product = self.cleaned_data.get("r_%s" % combo["hash"])
        new_product_pk = getattr(new_product, "pk", None)
        old_product_pk = combo["result_product_pk"]
        if old_product_pk == new_product_pk:  # Nothing to do
            return
        if old_product_pk:  # Unlink old one
            try:
                old_product = Product.objects.get(variation_parent=self.parent_product, pk=old_product_pk)
                old_product.unlink_from_parent()
            except ObjectDoesNotExist:
                pass
        if new_product:
            try:
                new_product.link_to_parent(parent=self.parent_product, combination_hash=combo["hash"])
            except ImpossibleProductModeException as ipme:
                six.raise_from(
                    Problem(_("Unable to link %(product)s: %(error)s.") % {"product": new_product, "error": ipme}), ipme
                )

    def save(self):
        if not self.has_changed():  # See `CustomerGroupPricingForm.save()`.
            return
        with atomic():
            for combo in self.parent_product.get_all_available_combinations():
                self._save_combo(combo)


class VariationVariablesDataForm(forms.Form):
    configuration_key = "saved_variation_templates"

    data = forms.CharField(widget=forms.HiddenInput(), required=False)
    activate_template = forms.BooleanField(
        required=False,
        label=_("Activate template"),
        help_text=_(
            "Enable this to activate a selected template. If no "
            "template is selected, variation data will be saved without "
            "checking, even if this setting is enabled."
        )
    )
    template_name = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.TextInput(attrs={'pattern': r'.*\S.*'})
    )

    def __init__(self, **kwargs):
        self.parent_product = kwargs.pop("parent_product", None)
        self.request = kwargs.pop("request", None)
        super(VariationVariablesDataForm, self).__init__(**kwargs)

    def get_variable_data(self):
        # This function is a little convoluted due to optimization.
        product = self.parent_product

        variables = {}  # All relevant ProductVariationVariables.

        # All encountered ProductVariationVariableValues.
        # These are the same dicts as are added into `variables[x].values`,
        # so updating these (as is done later) will modify `variables` as well.
        all_values = {}

        # Populate `variables` and `all_values`, but don't bother with translatable text just yet.
        for var in ProductVariationVariable.objects.filter(product=product).prefetch_related("values").all():
            values = []
            variables[var.pk] = {
                "pk": var.pk,
                "ordering": var.ordering,
                "identifier": var.identifier,
                "names": {},
                "values": values
            }
            for val in var.values.all():
                val_dict = {
                    "pk": val.pk,
                    "ordering": val.ordering,
                    "identifier": val.identifier,
                    "texts": {}  # The underlying field is "value", but that's confusing here
                }
                all_values[val.pk] = val_dict
                values.append(val_dict)

        # Now backfill in all translations.
        variable_xlate_model = ProductVariationVariable._parler_meta.root_model
        value_xlate_model = ProductVariationVariableValue._parler_meta.root_model
        assert issubclass(variable_xlate_model, Model)
        assert issubclass(value_xlate_model, Model)
        for var_id, language_code, name in (
                variable_xlate_model.objects.filter(master__in=variables).values_list("master", "language_code", "name")
        ):
            variables[var_id]["names"][language_code] = name

        for val_id, language_code, text in (
                value_xlate_model.objects.filter(master__in=all_values).values_list("master", "language_code", "value")
        ):
            all_values[val_id]["texts"][language_code] = text

        return sorted(variables.values(), key=lambda var: var["ordering"])

    def get_variation_templates(self, **kwargs):
        shop = get_shop(self.request)
        return configuration.get(shop, self.configuration_key, [])

    def get_editor_args(self):
        return {
            "languages": [
                {
                    "code": code,
                    "name": get_language_name(code)
                } for code in to_language_codes(
                    settings.LANGUAGES, getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", "en"))
                ],
            "variables": self.get_variable_data(),
            "templates": self.get_variation_templates()
        }

    def process_var_datum(self, var_datum, ordering):
        deleted = var_datum.get("DELETE")
        var = ProductVariationVariable(product=self.parent_product)
        if deleted:
            if var.pk:
                var.delete()
            return
        var.identifier = var_datum.get("identifier") or get_random_string()
        var.ordering = ordering
        var.save()
        for lang_code, name in var_datum["names"].items():
            var.set_current_language(lang_code)
            var.name = name
        var.save_translations()

        for ordering, val_datum in enumerate(var_datum["values"]):
            self.process_val_datum(var, val_datum, ordering)

        if not var.values.exists():  # All values gone, so delete the skeleton variable too
            var.delete()
            # thank mr skeltal

    def process_val_datum(self, var, val_datum, ordering):
        """
        :type var: ProductVariationVariable
        :type val_datum: dict
        """
        deleted = val_datum.get("DELETE")
        val = ProductVariationVariableValue(variable=var)
        if deleted:
            if val.pk:
                val.delete()
            return
        val.identifier = val_datum.get("identifier") or get_random_string()
        val.ordering = ordering
        val.save()
        for lang_code, text in val_datum["texts"].items():
            val.set_current_language(lang_code)
            val.value = text
        val.save_translations()

    def _save_template(self, data, identifier=None):
        shop = get_shop(self.request)
        saved_templates = self.get_variation_templates()
        if identifier:
            for template in saved_templates:
                if(template["identifier"] == identifier):
                    template["data"] = data  # Edit tempalte
        else:
            template_name = self.cleaned_data.get("template_name", _("Unnamed %s") % random.randint(1, 9999))
            payload = {
                "name": template_name,
                "identifier": template_name.lower().replace(" ", "_") + ("%s" % random.randint(1, 9999)),
                "data": data
            }
            saved_templates.append(payload)
        configuration.set(shop, self.configuration_key, saved_templates)

    def _activate_template(self, var_data, identifier):
        if self.change_template:
            ProductVariationVariable.objects.filter(
                product=self.parent_product).delete()  # former PVV objects need to be deleted!
        self.parent_product.clear_variation()
        for ordering, var_datum in enumerate(var_data):
            self.process_var_datum(var_datum, ordering)

    def save(self):
        template_data = json.loads(self.cleaned_data.get("data"))
        template_name = self.cleaned_data.get("template_name", "").strip()
        if not template_data:  # No data means the Mithril side hasn't been touched at all
            return
        self.change_template = False
        identifier = template_data.get("template_identifier", False)
        var_data = template_data.get("variable_values")
        activate_template = self.cleaned_data.get("activate_template", False)
        if template_name != "":
            var_data = []  # New template name is added so var data is empty
            identifier = False
            activate_template = False
        if identifier or template_name != "":
            self._save_template(var_data, identifier)
        if activate_template:
            self.change_template = True
            self._activate_template(var_data, identifier)
