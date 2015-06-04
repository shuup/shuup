# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django import forms

from shoop.core.models import Product, ShopProduct
from shoop.core.models.attributes import AttributeType, Attribute
from shoop.utils.i18n import get_language_name
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm, to_language_codes


class ProductBaseForm(MultiLanguageModelForm):
    class Meta:
        model = Product
        fields = (
            "accounting_identifier",
            "barcode",
            "category",
            "cost_center",
            "depth",
            "gross_weight",
            "gtin",
            "height",
            "manufacturer",
            "net_weight",
            "profit_center",
            "purchase_price",
            "sales_unit",
            "shipping_mode",
            "sku",
            "stock_behavior",
            "suggested_retail_price",
            "tax_class",
            "type",
            "width",
            # I18n
            "description",
            "keywords",
            "name",
            "status_text",
            "variation_name",
        )
        widgets = {
            "keywords": forms.TextInput()
        }


class ShopProductForm(forms.ModelForm):
    class Meta:
        model = ShopProduct
        fields = (
            "suppliers",
            "visible",
            "listed",
            "purchasable",
            "searchable",
            "visibility_limit",
            "visibility_groups",
            "purchase_multiple",
            "minimum_purchase_quantity",
            "limit_shipping_methods",
            "limit_payment_methods",
            "shipping_methods",
            "payment_methods",
            "primary_category",
            "categories",
            # TODO: "shop_primary_image",
        )


class ProductAttributesForm(forms.Form):
    def __init__(self, **kwargs):
        self.languages = to_language_codes(kwargs.pop("languages", ()))
        self.product = kwargs.pop("product")
        self.attributes = self.product.get_available_attribute_queryset()
        super(ProductAttributesForm, self).__init__(**kwargs)
        if self.product.pk:
            self.applied_attrs = dict((pa.attribute_id, pa) for pa in self.product.attributes.all())
        else:
            self.applied_attrs = {}
        self._field_languages = {}
        self._build_fields()

    def _build_fields(self):
        for attribute in self.attributes:
            self._field_languages[attribute.identifier] = {}
            pa = self.applied_attrs.get(attribute.pk)
            if attribute.type == AttributeType.TRANSLATED_STRING:
                self._process_multilang_attr(attribute, pa)
            else:
                self.fields[attribute.identifier] = attribute.formfield()
                if pa:
                    if attribute.type == AttributeType.TIMEDELTA:  # Special case.
                        value = pa.numeric_value
                    else:
                        value = pa.value
                    self.initial[attribute.identifier] = value
                self._field_languages[attribute.identifier][None] = attribute.identifier

    def _process_multilang_attr(self, attribute, pa):
        languages = tuple(self.languages)
        if pa:  # Ensure the fields for languages in the database but not currently otherwise available are visible
            extant_languages = pa.get_available_languages()
            languages += tuple(lang for lang in extant_languages if lang not in languages)
        else:
            extant_languages = set()
        for lang in languages:
            field_name = "%s__%s" % (attribute.identifier, lang)
            self.fields[field_name] = field = attribute.formfield()
            field.label = "%s [%s]" % (field.label, get_language_name(lang))

            if pa and lang in extant_languages:
                self.initial[field_name] = getattr(
                    pa.get_translation(lang), "translated_string_value", None
                )
            self._field_languages[attribute.identifier][lang] = field_name

    def save(self):
        for attribute in self.attributes:
            for language, field_name in self._field_languages[attribute.identifier].items():
                value = self.cleaned_data.get(field_name)
                if attribute.is_translated and not value:
                    value = ""
                try:
                    self.product.set_attribute_value(attribute.identifier, value, language)
                except Attribute.DoesNotExist:
                    # This may occur when the user changes a product type (the attribute is no longer in
                    # `product.get_available_attribute_queryset()`. In this case, we just drop the assignment.
                    # TODO: Should we maybe _not_ drop the assignment?
                    pass
        self.product.clear_attribute_cache()
