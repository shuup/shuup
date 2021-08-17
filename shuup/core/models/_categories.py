# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.db import models
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from mptt.querysets import TreeQuerySet
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableManager, TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.core.signals import category_deleted
from shuup.core.utils.slugs import generate_multilanguage_slugs
from shuup.utils.analog import LogEntryKind, define_log_model


class CategoryStatus(Enum):
    INVISIBLE = 0
    VISIBLE = 1
    DELETED = 2

    class Labels:
        INVISIBLE = _("invisible")
        VISIBLE = _("visible")
        DELETED = _("deleted")


class CategoryVisibility(Enum):
    VISIBLE_TO_ALL = 1
    VISIBLE_TO_LOGGED_IN = 2
    VISIBLE_TO_GROUPS = 3

    class Labels:
        VISIBLE_TO_ALL = _("visible to all")
        VISIBLE_TO_LOGGED_IN = _("visible to logged-in customers")
        VISIBLE_TO_GROUPS = _("visible to certain customer groups")


class CategoryQuerySet(TranslatableQuerySet, TreeQuerySet):
    pass


class CategoryManager(TreeManager, TranslatableManager):
    queryset_class = CategoryQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db).order_by(self.tree_id_attr, self.left_attr)

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
                    Q(visibility__in=(CategoryVisibility.VISIBLE_TO_ALL, CategoryVisibility.VISIBLE_TO_LOGGED_IN))
                    | Q(visibility_groups__in=customer.groups.all())
                )
            else:
                qs = qs.filter(visibility=CategoryVisibility.VISIBLE_TO_ALL)

        return qs.distinct()

    def all_except_deleted(self, language=None, shop=None):
        qs = (self.language(language) if language else self).exclude(status=CategoryStatus.DELETED)
        if shop:
            qs = qs.filter(shops=shop)
        return qs


@python_2_unicode_compatible
class Category(MPTTModel, TranslatableModel):
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent category"),
        on_delete=models.CASCADE,
        help_text=_("If your category is a sub-category of another category, you can link them here."),
    )
    shops = models.ManyToManyField(
        "Shop",
        blank=True,
        related_name="categories",
        verbose_name=_("shops"),
        help_text=_("You can select which shops the category is visible in."),
    )
    identifier = InternalIdentifierField(unique=True)
    status = EnumIntegerField(
        CategoryStatus,
        db_index=True,
        verbose_name=_("status"),
        default=CategoryStatus.VISIBLE,
        help_text=_("Choose if you want this category to be visible in your store."),
    )
    image = FilerImageField(
        verbose_name=_("image"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Category image. Will be shown in places defined by the graphical theme in use."),
    )
    ordering = models.IntegerField(
        default=0,
        verbose_name=_("ordering"),
        help_text=_(
            "You can assign numerical values to images to tell the order in which they "
            "shall be displayed on the vendor page. You can also use the `Organize` "
            "button in the list view to order them visually with a drag-and-drop."
        ),
    )
    visibility = EnumIntegerField(
        CategoryVisibility,
        db_index=True,
        default=CategoryVisibility.VISIBLE_TO_ALL,
        verbose_name=_("visibility limitations"),
        help_text=_(
            "You can choose to limit who sees your category based on whether they are logged in or if they are "
            "part of a certain customer group."
        ),
    )
    visible_in_menu = models.BooleanField(
        verbose_name=_("visible in menu"),
        default=True,
        help_text=_("Enable if this category should be visible in the store front's menu."),
    )
    visibility_groups = models.ManyToManyField(
        "ContactGroup",
        blank=True,
        verbose_name=_("visible for groups"),
        related_name=u"visible_categories",
        help_text=_(
            "Select the customer groups you want to see this category. "
            "There are three groups created by default: Company, Person, Anonymous. "
            "In addition you can also define custom groups by searching for `Contact Groups`."
        ),
    )

    translations = TranslatedFields(
        name=models.CharField(
            max_length=128,
            verbose_name=_("name"),
            db_index=True,
            help_text=_(
                "Enter a descriptive name for your product category. "
                "Products can be found in the store front under the defined product category "
                "either directly in menus or while searching."
            ),
        ),
        description=models.TextField(
            verbose_name=_("description"),
            blank=True,
            help_text=_(
                "Give your product category a detailed description. "
                "This will help shoppers find your products under that category in your store and on the web."
            ),
        ),
        slug=models.SlugField(
            blank=True,
            null=True,
            verbose_name=_("slug"),
            help_text=_(
                "Enter a URL slug for your category. Slug is user- and search engine-friendly short text "
                "used in a URL to identify and describe a resource. In this case it will determine "
                "what your product category page URL in the browser address bar will look like. "
                "A default will be created using the category name."
            ),
        ),
    )

    objects = CategoryManager()

    class Meta:
        ordering = ("tree_id", "lft")
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    class MPTTMeta:
        order_insertion_by = ["ordering"]

    def __str__(self):
        return self.get_hierarchy()

    def get_hierarchy(self, reverse=True):
        return " / ".join(
            list(
                filter(
                    None,
                    [
                        ancestor.safe_translation_getter("name", any_language=True) or ancestor.identifier
                        for ancestor in self.get_ancestors(ascending=reverse, include_self=True).prefetch_related(
                            "translations"
                        )
                    ],
                )
            )
        )

    def get_cached_children(self):
        from shuup.core import cache

        key = "category_cached_children:{}".format(self.pk)
        children = cache.get(key)
        if children is not None:
            return children
        children = self.get_children()
        cache.set(key, children)
        return children

    def is_visible(self, customer):
        if customer and customer.is_all_seeing:
            return self.status != CategoryStatus.DELETED
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
    def _get_slug_name(self, translation):
        if self.status == CategoryStatus.DELETED:
            return None
        return getattr(translation, "name", self.pk)

    def delete(self, using=None):
        raise NotImplementedError(
            "Error! Not implemented: `Category` -> `delete()`. Use `soft_delete()` for categories."
        )

    @atomic
    def soft_delete(self, user=None):
        if not self.status == CategoryStatus.DELETED:
            for shop_product in self.primary_shop_products.all():
                shop_product.categories.remove(self)
                shop_product.primary_category = None
                shop_product.save()
            for shop_product in self.shop_products.all():
                shop_product.categories.remove(self)
                shop_product.primary_category = None
                shop_product.save()
            for child in self.children.all():
                child.parent = None
                child.save()
            self.status = CategoryStatus.DELETED
            self.add_log_entry("Success! Deleted (soft).", kind=LogEntryKind.DELETION, user=user)
            self.save()
            category_deleted.send(sender=type(self), category=self)

    def save(self, *args, **kwargs):
        rv = super(Category, self).save(*args, **kwargs)
        generate_multilanguage_slugs(self, self._get_slug_name)

        # bump children cache
        from shuup.core import cache

        cache.bump_version("category_cached_children")

        return rv


CategoryLogEntry = define_log_model(Category)
