# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal
from django import forms
from django.db.models import Max, Min
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.db.models import Q, Count
from shuup.core.models import (
    Category,
    Attribute,
    Product,
    ProductAttribute,
    AttributeType,
    ShopProduct,
)
from shuup.admin.shop_provider import get_shop
from shuup.front.utils.sorts_and_filters import ProductListFormModifier
from shuup.admin.forms.widgets import (
    QuickAddCategoryMultiSelect,
)
from .models import (
    BasicFilterSettingsModel,
    BasicAttributesFilterSettingsModel,
    CategoriesFilterSettingsModel,
    AttributesFilterSettingsModel,
    BASIC_ATTRIBUTE_FIELDS,
)


class BaseFilterSettingsForm(forms.ModelForm):
    class Meta:
        model = BasicFilterSettingsModel
        exclude = ("shop",)


class CategoriesFilterSettingsForm(forms.ModelForm):
    class Meta:
        model = CategoriesFilterSettingsModel
        exclude = ("shop",)
        widgets = {
            "category": QuickAddCategoryMultiSelect,
        }


class AttributesFilterSettingsForm(forms.ModelForm):
    class Meta:
        model = AttributesFilterSettingsModel
        exclude = (
            "attribute",
            "enabled",
            "shop")

    def __init__(self, *args, **kwargs):
        super(AttributesFilterSettingsForm, self).__init__(*args, **kwargs)

        self.attributes = Attribute.objects.filter(
            visibility_mode__in=[1, 2],
        )

        for base_attr in BASIC_ATTRIBUTE_FIELDS:
            enabled_attr = "enabled-%s" % (base_attr)
            self.fields[enabled_attr] = forms.BooleanField(
                required=False,
            )
            base_attr_label = base_attr.replace("_", " ").capitalize()
            self.fields[enabled_attr].label = base_attr_label

        for attr in self.attributes:
            bool_field = "enabled_%s" % (attr.id)
            self.fields[bool_field] = forms.BooleanField(
                required=False,
            )
            self.fields[bool_field].label = attr.name


class ProductFilterForm(ProductListFormModifier):
    basic_fields = [
        'width', 'height', 'depth', 'net_weight',
        'gross_weight', 'manufacturer',
    ]

    def should_use(self, configuration):
        return True

    def get_ordering(self, configuration):
        return 0

    def get_label(self, field_label, attr_type):

        if attr_type is AttributeType.BOOLEAN:
            if field_label == "1":
                field_label = _("Yes")
            elif field_label == "0":
                field_label = _("No")

        return field_label

    def get_categories(self, request):
        categories = None
        settings_categories = CategoriesFilterSettingsModel.objects\
            .values("category", "category__translations__name")\
            .filter(shop=get_shop(request))\
            .exclude(category__id__isnull=True)

        if settings_categories:
            category_choices = []

            for category in settings_categories:
                category_choices.append(
                    [
                        category["category"],
                        category["category__translations__name"],
                    ]
                )
            category_choices.insert(0, [0, _("All categories")])
            categories = ("category",
                          forms.ChoiceField(label=_("Category"),
                                            choices=category_choices,
                                            required=False)
                          )

        return categories

    def get_manufacturers(self, request):
        manufacturers = None
        settings_manufacturers = Product.objects.listed(
            shop=get_shop(request), language=get_language()
        ).select_related("manufacturer").exclude(manufacturer_id__isnull=True)

        if settings_manufacturers:
            manufacturers_choices = []

            for manufacturers in settings_manufacturers:
                manufacturers_choices.append(
                    [
                        manufacturers.manufacturer_id,
                        manufacturers.manufacturer.name,
                    ]
                )
            manufacturers_choices.insert(0, [0, _("All manufacturers")])
            manufacturers = ("manufacturer",
                             forms.ChoiceField(label=_("Manufacturers"),
                                               choices=manufacturers_choices,
                                               required=False)
                             )

        return manufacturers

    def get_basic_attributes(self, request):
        basic_attributes = []
        basic_attrs_settings = BasicAttributesFilterSettingsModel.objects.filter(
            enabled=True,
            shop=get_shop(request),
        ).values_list(
            'attribute_name',
            flat=True
        ).exclude(
            attribute_name__in=['default_price', 'manufacturer_id', 'manufacturer']
        )

        settings_basic_attributes = Product.objects.listed(
            shop=get_shop(request), language=get_language()
        ).values(*basic_attrs_settings).distinct()

        if settings_basic_attributes:
            for basic_attribute in settings_basic_attributes:
                for key, value in basic_attribute.items():
                    if value:
                        basic_attr_label = str(round(value))
                        basic_attr_value = key + '__' + basic_attr_label
                        basic_attributes.append([basic_attr_value, forms.BooleanField(
                            widget=forms.CheckboxInput(
                                attrs={'data-accordion-group': _(key.replace('_', ' '))}
                            ),
                            label=basic_attr_label,
                            required=False)
                        ])

        return basic_attributes

    def get_attributes(self, request):
        attributes = []

        attr_filters_ids = AttributesFilterSettingsModel.objects.filter(
            shop=get_shop(request),
            enabled=True,
        )
        settings_attributes = ProductAttribute.objects\
            .select_related("attribute")\
            .filter(untranslated_string_value__isnull=False)

        if settings_attributes:
            c = 0
            for attribute in settings_attributes:
                if attribute.untranslated_string_value:
                    attr_value = str(attribute.untranslated_string_value)
                    attr_id = str(attribute.attribute_id)
                    attr_field_name = attr_id + '__' + attr_value
                    attributes.append([attr_field_name, forms.BooleanField(
                        widget=forms.CheckboxInput(
                            attrs={'data-accordion-group': attribute.attribute.name}
                        ),
                        label=self.get_label(attr_value, attribute.attribute.type),
                        required=False),
                    ])
                c += 1

        return attributes

    def get_price(self):
        price_ranges = []
        max_price = ShopProduct.objects.all().aggregate(Max('default_price_value'))

        max_value = round(max_price['default_price_value__max'])
        substruct_value = max_value / 4

        for p in range(1, 5):
            min_value = max_value - round(substruct_value)
            if max_value > min_value and min_value > 0:
                range_label = str(min_value) + ' - ' + str(max_value)
            else:
                range_label = '0' + ' - ' + str(max_value)

            price_ranges.append(['price__'+range_label, forms.BooleanField(
                widget=forms.CheckboxInput(
                    attrs={'data-accordion-group': _('price')}
                ),
                label=range_label,
                required=False),
            ])

            max_value = min_value

        return price_ranges

    def get_fields(self, request, category=None):
        fields = []

        categories = self.get_categories(request)
        if categories:
            fields.append(categories)

        manufacturers = self.get_manufacturers(request)
        if manufacturers:
            fields.append(manufacturers)

        basic_attributes = self.get_basic_attributes(request)
        if basic_attributes:
            for basic_attr_field in basic_attributes:
                fields.append(basic_attr_field)

        attributes = self.get_attributes(request)
        if attributes:
            for attr_field in attributes:
                fields.append(attr_field)

        prices_ranges = self.get_price()
        for pr in prices_ranges:
            fields.append(pr)

        return fields

    def get_search_product_ids(self, request, query_dict):
        product_ids = []
        if 'basic_attributes' in query_dict:
            product_ids += Product.objects.filter(
                **query_dict['basic_attributes']
            ).distinct().values_list("id", flat=True)
        if 'categories' in query_dict:
            product_ids += ShopProduct.objects.filter(
                **{
                    'categories': query_dict['categories'],
                    'shop': get_shop(request)
                }
            ).distinct().values_list("product", flat=True)
        if 'price_ranges' in query_dict:
            product_ids += ShopProduct.objects.filter(
                query_dict['price_ranges'],
                shop=get_shop(request)
            ).distinct().values_list("product", flat=True)
        if 'custom_attributes' in query_dict:
            product_ids += ProductAttribute.objects.filter(
                query_dict['custom_attributes'],
            ).distinct().values_list("product_id", flat=True)

        return product_ids

    def get_basic_attributes_query(self, data_key, data_value):
        basic_attributes = {}

        if query_key in basic_attributes:
            basic_attributes[query_key].append(data_value)
        else:
            basic_attributes[query_key] = [data_value]

        return basic_attributes

    def get_price_query(self, data_value):
        price_ranges = ''
        if " - " in data_value:
            price_values = data_value.split(" - ")
            min_value = Decimal(price_values[0])
            max_value = Decimal(price_values[1])
            if price_ranges == '':
                price_ranges = Q(default_price_value__range=(min_value, max_value))
            else:
                price_ranges |= Q(default_price_value__range=(min_value, max_value))
        return price_ranges

    def get_custom_attributes_query(self, data_key, data_value):
        custom_attributes = ''
        if custom_attributes == '':
            custom_attributes = Q(
                attribute_id=data_key,
                untranslated_string_value=data_value,
            )
        else:
            custom_attributes |= Q(
                attribute_id=data_key,
                untranslated_string_value=data_value,
            )
        return custom_attributes

    def get_compiled_attribute_query(self, data):
        query_dict = {}
        for key, value in data.items():
            if value and '__' in key:
                query_values = data_key.split("__")
                if query_values[0] in ['width', 'height', 'depth',
                                       'net_weight', 'gross_weight']:
                    query_dict.update(
                        {'basic_attributes': self.get_basic_attributes_query(
                            query_values[0], query_values[1]
                        )}
                    )
                elif query_values[0] == 'price':
                    query_dict.update(
                        {'price_ranges': self.get_price_query(
                            query_values[1]
                        )}
                    )
                else:
                    query_dict.update(
                        {'custom_attributes': self.get_custom_attributes_query(
                            query_values[0], query_values[1]
                        )}
                    )

        return query_dict

    def get_filters(self, request, data):
        query = {}
        data.pop("q")
        data.pop("sort")

        query = self.get_compiled_attribute_query(data)

        if 'category' in data:
            if data['category'] == '' or data['category'] == '0':
                data.pop("category")
            else:
                query.update({'categories': data['category']})

        if 'manufacturer' in data:
            if data['manufacturer'] == '' or data['manufacturer'] == '0':
                data.pop("manufacturer")
            else:
                query.update(
                        {
                            'basic_attributes': {
                                'manufacturer': int(data['manufacturer'])
                                }
                        }
                )

        if query:
            return Q(pk__in=self.get_search_product_ids(request, query))
        else:
            return Q()
