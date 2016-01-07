# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from parler.models import (
    TranslatableManager, TranslatableModel, TranslatedFields
)

from shoop.core.fields import InternalIdentifierField
from shoop.core.utils.slugs import generate_multilanguage_slugs
from shoop.utils.analog import define_log_model


class CategoryStatus(Enum):
    INVISIBLE = 0
    VISIBLE = 1
    DELETED = 2

    class Labels:
        INVISIBLE = _('invisible')
        VISIBLE = _('visible')
        DELETED = _('deleted')


class CategoryVisibility(Enum):
    VISIBLE_TO_ALL = 1
    VISIBLE_TO_LOGGED_IN = 2
    VISIBLE_TO_GROUPS = 3

    class Labels:
        VISIBLE_TO_ALL = _('visible to all')
        VISIBLE_TO_LOGGED_IN = _('visible to logged in customers')
        VISIBLE_TO_GROUPS = _('visible to certain customer groups')


class CategoryManager(TranslatableManager, TreeManager):

    def all_visible(self, customer, shop=None, language=None):
        root = (self.language(language) if language else self).all()

        if shop:
            root = root.filter(shops=shop)

        if customer and customer.is_all_seeing:
            qs = root.exclude(status=CategoryStatus.DELETED)
        else:
            qs = root.filter(status=CategoryStatus.VISIBLE)
            if customer and not customer.is_anonymous:
                qs = qs.filter(
                    Q(visibility__in=(CategoryVisibility.VISIBLE_TO_ALL, CategoryVisibility.VISIBLE_TO_LOGGED_IN)) |
                    Q(visibility_groups__in=customer.groups.all())
                )
            else:
                qs = qs.filter(visibility=CategoryVisibility.VISIBLE_TO_ALL)

        return qs.order_by("tree_id", "lft")

    def all_except_deleted(self, language=None):
        return (self.language(language) if language else self).exclude(status=CategoryStatus.DELETED)


@python_2_unicode_compatible
class Category(MPTTModel, TranslatableModel):
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children',
        verbose_name=_('parent category'), on_delete=models.CASCADE)
    shops = models.ManyToManyField("Shop", blank=True, related_name="categories")
    identifier = InternalIdentifierField(unique=True)
    status = EnumIntegerField(CategoryStatus, db_index=True, verbose_name=_('status'), default=CategoryStatus.INVISIBLE)
    image = FilerImageField(verbose_name=_('image'), blank=True, null=True, on_delete=models.SET_NULL)
    ordering = models.IntegerField(default=0, verbose_name=_('ordering'))
    visibility = EnumIntegerField(
        CategoryVisibility, db_index=True, default=CategoryVisibility.VISIBLE_TO_ALL,
        verbose_name=_('visibility limitations')
    )
    visibility_groups = models.ManyToManyField(
        "ContactGroup", blank=True, verbose_name=_('visible for groups'), related_name=u"visible_categories"
    )

    translations = TranslatedFields(
        name=models.CharField(max_length=128, verbose_name=_('name')),
        description=models.TextField(verbose_name=_('description'), blank=True),
        slug=models.SlugField(blank=True, null=True, verbose_name=_('slug'))
    )

    objects = CategoryManager()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    class MPTTMeta:
        order_insertion_by = ["ordering"]

    def __str__(self):
        return self.safe_translation_getter("name", any_language=True)

    def is_visible(self, customer):
        if customer and customer.is_all_seeing:
            return (self.status != CategoryStatus.DELETED)
        if self.status != CategoryStatus.VISIBLE:
            return False
        if not customer or customer.is_anonymous:
            if self.visibility != CategoryVisibility.VISIBLE_TO_ALL:
                return False
        else:
            if self.visibility == CategoryVisibility.VISIBLE_TO_GROUPS:
                group_ids = customer.groups.all().values_list("id", flat=True)
                return self.visibility_groups.filter(id__in=group_ids).exists()
        return True

    @staticmethod
    def _get_slug_name(self):
        if self.status == CategoryStatus.DELETED:
            return None
        return self.safe_translation_getter("name")

    def save(self, *args, **kwargs):
        rv = super(Category, self).save(*args, **kwargs)
        generate_multilanguage_slugs(self, self._get_slug_name)
        return rv

CategoryLogEntry = define_log_model(Category)
