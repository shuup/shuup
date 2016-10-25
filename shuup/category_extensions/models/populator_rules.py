# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField

from shuup.core.models import (
    Attribute, Manufacturer, PolymorphicShuupModel, ProductAttribute
)
from shuup.utils.enums import ComparisonOperator


class CategoryPopulatorRule(PolymorphicShuupModel):
    pass


class AttributePopulatorRule(CategoryPopulatorRule):
    identifier = "attribute_populator"

    attribute = models.OneToOneField(Attribute, verbose_name="attribute")
    operator = EnumIntegerField(
        ComparisonOperator, default=ComparisonOperator.GTE, verbose_name=_("operator"))

    product_attr_name = models.CharField(max_length=255, verbose_name="product attribute name")

    def matches(self, shop_product):
        value = getattr(shop_product, self.product_attr_name, None)
        if not value:
            value = getattr(shop_product.product, self.product_attr_name, None)
        try:
            pa = ProductAttribute.objects.get(attribute=self.attribute, product=shop_product.product)
            if self.operator == ComparisonOperator.LTE:
                return (pa.value <= value)
            elif self.operator == ComparisonOperator.EQUALS:
                return (pa.value == value)
            return (pa.value >= value)
        except ProductAttribute.DoesNotExist:
            return False

    def filter_matches(self, queryset):
        excludes = []
        for shop_product in queryset.all():
            if not self.matches(shop_product):
                excludes.append(shop_product.pk)
        return queryset.exclude(pk__in=excludes)


class ManufacturerPopulatorRule(CategoryPopulatorRule):
    identifier = "manufacturer_populator"

    manufacturers = models.ManyToManyField(Manufacturer, verbose_name="manufacturer")

    def matches(self, shop_product):
        return (shop_product.product.manufacturer in self.manufacturers.all())

    def filter_matches(self, queryset):
        return queryset.filter(product__manufacturer__in=self.manufacturers.all())


class CreationDatePopulatorRule(CategoryPopulatorRule):
    identifier = "creationdate_populator"

    start_date = models.DateField(verbose_name="start date")
    end_date = models.DateField(verbose_name="end date")

    def matches(self, shop_product):
        return (self.start_date <= shop_product.product.created_on.date() <= self.end_date)

    def filter_matches(self, queryset):
        return queryset.exclude(product__created_on__gt=self.start_date).exclude(product__created_on__lt=self.end_date)
