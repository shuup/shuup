# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import defaultdict

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet
from django.forms.formsets import DEFAULT_MAX_NUM, DEFAULT_MIN_NUM
from django.utils.translation import ugettext_lazy as _
from filer.models import Image

from shuup.admin.forms.widgets import ImageChoiceWidget, MediaChoiceWidget
from shuup.core.models import (
    Attribute, AttributeType, Category, Product, ProductMedia,
    ProductMediaKind, Shop, ShopProduct
)
from shuup.utils.i18n import get_language_name
from shuup.utils.multilanguage_model_form import (
    MultiLanguageModelForm, to_language_codes
)


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
            "sales_unit",
            "shipping_mode",
            "sku",
            "stock_behavior",
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

    def __init__(self, **kwargs):
        super(ProductBaseForm, self).__init__(**kwargs)
        self.fields["sales_unit"].required = True  # TODO: Move this to model
        self.fields["category"].queryset = Category.objects.all_except_deleted()


class ShopProductForm(forms.ModelForm):
    class Meta:
        model = ShopProduct
        fields = (
            "default_price_value",
            "minimum_price_value",
            "suppliers",
            "visibility",
            "purchasable",
            "visibility_limit",
            "visibility_groups",
            "purchase_multiple",
            "minimum_purchase_quantity",
            "backorder_maximum",
            "limit_shipping_methods",
            "limit_payment_methods",
            "shipping_methods",
            "payment_methods",
            "primary_category",
            "categories",
            # TODO: "shop_primary_image",
        )
        help_texts = {
            "backorder_maximum": _("Number of units that can be purchased after the product is out of stock. "
                                   "Set to blank for product to be purchasable without limits")
        }

    def __init__(self, **kwargs):
        super(ShopProductForm, self).__init__(**kwargs)
        category_qs = Category.objects.all_except_deleted()
        self.fields["default_price_value"].required = True
        self.fields["primary_category"].queryset = category_qs
        self.fields["categories"].queryset = category_qs

    # TODO: Move this to model
    def clean_minimum_purchase_quantity(self):
        minimum_purchase_quantity = self.cleaned_data.get("minimum_purchase_quantity")
        if minimum_purchase_quantity <= 0:
            raise ValidationError(_("Minimum Purchase Quantity must be greater than 0."))
        return minimum_purchase_quantity

    def clean_backorder_maximum(self):
        backorder_maximum = self.cleaned_data.get("backorder_maximum")
        if backorder_maximum is not None and backorder_maximum < 0:
            raise ValidationError(_("Backorder maximum must be greater than or equal to 0."))
        return backorder_maximum


class ProductAttributesForm(forms.Form):
    def __init__(self, **kwargs):
        self.languages = to_language_codes(kwargs.pop("languages", ()))
        self.language_names = dict((lang, get_language_name(lang)) for lang in self.languages)
        self.product = kwargs.pop("product")
        self.attributes = self.product.get_available_attribute_queryset()
        self.trans_name_map = defaultdict(dict)
        self.translated_field_names = []
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
            self.trans_name_map[lang][field_name] = field_name
            self.translated_field_names.append(field_name)

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


class BaseProductMediaForm(MultiLanguageModelForm):
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
        super(BaseProductMediaForm, self).__init__(**kwargs)

        self.fields["file"].widget = MediaChoiceWidget()  # Filer misimplemented the field; we need to do this manually.
        self.fields["file"].required = True

        if self.allowed_media_kinds:
            # multiple media kinds allowed, filter the choices list to reflect the `self.allowed_media_kinds`
            allowed_kinds_values = set(v.value for v in self.allowed_media_kinds)
            self.fields["kind"].choices = [
                (value, choice)
                for value, choice in self.fields["kind"].choices
                if value in allowed_kinds_values
            ]

            if len(self.allowed_media_kinds) == 1:
                # only one media kind given, no point showing the dropdown
                self.fields["kind"].widget = forms.HiddenInput()

            self.fields["kind"].initial = self.allowed_media_kinds[0]

        if not self.instance.pk:
            self.fields["shops"].initial = [default_shop]

        self.file_url = self.instance.url

    def get_thumbnail(self, request):
        """
        Get thumbnail url.

        If thumbnail creation fails for whatever reason,
        an error message is displayed for user.
        """
        try:
            thumbnail = self.instance.get_thumbnail()
        except Exception as error:
            msg = _("Thumbnail generation of %(media)s failed: %(error)s") % {"media": self.instance, "error": error}
            messages.error(request, msg)
            thumbnail = None
        return thumbnail

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


class ProductMediaForm(BaseProductMediaForm):
    def __init__(self, **kwargs):
        super(ProductMediaForm, self).__init__(**kwargs)
        self.fields["file"].required = False

    def clean_external_url(self):
        external_url = self.cleaned_data.get("external_url")

        # if form has been deleted, we don't want to validate fields
        if "DELETE" in self.changed_data:
            return external_url

        file = self.cleaned_data.get("file")
        if external_url and file:
            raise ValidationError(_("Use only URL or file, not both"))
        return external_url


class ProductMediaFormSet(BaseProductMediaFormSet):
    form_class = ProductMediaForm
    allowed_media_kinds = [ProductMediaKind.GENERIC_FILE, ProductMediaKind.DOCUMENTATION, ProductMediaKind.SAMPLE]


class ProductImageMediaForm(BaseProductMediaForm):
    is_primary = forms.BooleanField(required=False, label=_("Is primary"))

    def __init__(self, **kwargs):
        super(ProductImageMediaForm, self).__init__(**kwargs)
        self.fields["file"].widget = ImageChoiceWidget()

        if self.instance.pk and self.instance.file:
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

    def save(self, commit=True):
        """
        Save the form.

        In addition add the first saved image as primary image for the
        product if none is selected as such.
        """
        super(ProductImageMediaFormSet, self).save(commit)

        has_primary = any(form.cleaned_data.get("is_primary") for form in (self.forms or []))
        eligible_forms = [form for form in (self.forms or []) if
                          (form.cleaned_data.get("file") and not form.cleaned_data.get("DELETE"))]

        if eligible_forms and not has_primary:
            # make first form be the primary image as well
            form_instance = self.forms[0]
            form_instance.product.primary_image = form_instance.instance
            form_instance.product.save()
