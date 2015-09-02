# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet
from django.forms.formsets import DEFAULT_MAX_NUM, DEFAULT_MIN_NUM
from django.utils.translation import ugettext_lazy as _
from filer.models import Image

from shoop.admin.forms.widgets import MediaChoiceWidget
from shoop.core.models import Attribute, AttributeType, Product, ProductMedia, ProductMediaKind, Shop, ShopProduct
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
            "default_price",
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
        if not self.has_changed():  # Nothing to do, don't bother iterating
            return
        for attribute in self.attributes:
            for language, field_name in self._field_languages[attribute.identifier].items():
                if field_name not in self.cleaned_data:
                    continue
                value = self.cleaned_data[field_name]
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


class ProductMediaForm(MultiLanguageModelForm):
    class Meta:
        model = ProductMedia
        fields = (
            "file",
            "ordering",
            "external_url",
            "public",
            "title",
            "description",
            "purchased",
            "shops",
            "kind"
        )

    def __init__(self, **kwargs):
        self.product = kwargs.pop("product")
        self.allowed_media_kinds = kwargs.pop("allowed_media_kinds")
        default_shop = kwargs.pop("default_shop")
        super(ProductMediaForm, self).__init__(**kwargs)

        self.fields["file"].widget = MediaChoiceWidget()  # Filer misimplemented the field; we need to do this manually.
        self.fields["file"].required = True

        if len(self.allowed_media_kinds) == 1:
            # only one media kind given, no point showing the dropdown
            self.fields["kind"].initial = self.allowed_media_kinds[0]
            self.fields["kind"].widget = forms.HiddenInput()

        if not self.instance.pk:
            self.fields["shops"].initial = [default_shop]

        self.file_url = self.instance.url
        self.thumbnail = None

    def pre_master_save(self, instance):
        instance.product = self.product


class BaseProductMediaFormSet(BaseModelFormSet):
    validate_min = False
    min_num = DEFAULT_MIN_NUM
    validate_max = False
    max_num = DEFAULT_MAX_NUM
    absolute_max = DEFAULT_MAX_NUM
    model = ProductMedia
    can_delete = True
    can_order = False
    extra = 1

    allowed_media_kinds = []

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop("product")
        self.languages = to_language_codes(kwargs.pop("languages", ()))
        kwargs.pop("empty_permitted")  # this is unknown to formset
        super(BaseProductMediaFormSet, self).__init__(*args, **kwargs)

    def get_queryset(self):
        qs = ProductMedia.objects.filter(product=self.product)
        if self.allowed_media_kinds:
            qs = qs.filter(kind__in=self.allowed_media_kinds)
        return qs

    def form(self, **kwargs):
        kwargs.setdefault("languages", self.languages)
        kwargs.setdefault("product", self.product)
        kwargs.setdefault("allowed_media_kinds", self.allowed_media_kinds)
        kwargs.setdefault("default_shop", Shop.objects.first().pk)
        return self.form_class(**kwargs)


class ProductMediaFormSet(BaseProductMediaFormSet):
    form_class = ProductMediaForm


class ProductImageMediaForm(ProductMediaForm):
    is_primary = forms.BooleanField(required=False)

    def __init__(self, **kwargs):
        super(ProductImageMediaForm, self).__init__(**kwargs)
        if self.instance.pk and self.instance.file:
            if isinstance(self.instance.file, Image):
                thumbnail = self.instance.easy_thumbnails_thumbnailer.get_thumbnail({
                    'size': (64, 64),
                    'crop': True,
                    'upscale': True,
                })
                self.file_url = self.instance.url
                self.thumbnail = thumbnail.url or None
            if self.product.primary_image_id == self.instance.pk:
                self.fields["is_primary"].initial = True

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file and not isinstance(file, Image):
            raise ValidationError(_("Only images allowed in this field"))
        return file

    def save(self, commit=True):
        instance = super(ProductImageMediaForm, self).save(commit)
        if self.cleaned_data.get("is_primary"):
            self.product.primary_image = instance
            self.product.save()
        return instance


class ProductImageMediaFormSet(ProductMediaFormSet):
    allowed_media_kinds = [ProductMediaKind.IMAGE]
    form_class = ProductImageMediaForm
