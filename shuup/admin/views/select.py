# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from shuup.core.models import (
    Carrier, Contact, Product, ProductMode, Shop, ShopProductVisibility
)


def _field_exists(model, field):
    try:
        model._meta.get_field(field)
        return True
    except FieldDoesNotExist:
        return False


class MultiselectAjaxView(TemplateView):
    model = None
    search_fields = []
    result_limit = 20

    def init_search_fields(self, cls):
        """
        Configure the fields to use for searching.

        If the `cls` object has a search_fields attribute, it will be used,
        otherwise, the class will be inspected and the attribute
        `name` or `translations__name` will mainly be used.

        Other fields will be used for already known `cls` instances.
        """
        if hasattr(cls, "search_fields"):
            self.search_fields = cls.search_fields
            return

        self.search_fields = []
        key = "%sname" % ("translations__" if hasattr(cls, "translations") else "")
        self.search_fields.append(key)

        if issubclass(cls, Carrier):
            self.search_fields.append("base_translations__name")
            self.search_fields.remove("name")
        if issubclass(cls, Contact):
            self.search_fields.append("email")
        if issubclass(cls, Product):
            self.search_fields.append("sku")
            self.search_fields.append("barcode")

        user_model = get_user_model()
        if issubclass(cls, user_model):
            if _field_exists(user_model, "username"):
                self.search_fields.append("username")
            if _field_exists(user_model, "email"):
                self.search_fields.append("email")
            if not _field_exists(user_model, "name"):
                self.search_fields.remove("name")

    def get_data(self, request, *args, **kwargs):
        model_name = request.GET.get("model")
        if not model_name:
            return []

        cls = apps.get_model(model_name)
        qs = cls.objects.all()
        shop = self.request.shop
        qs = self._filter_query(cls, qs, shop, getattr(request.user, "is_superuser", False))
        self.init_search_fields(cls)
        if not self.search_fields:
            return [{"id": None, "name": _("Couldn't get selections for %s.") % model_name}]

        if request.GET.get("search"):
            query = Q()
            keyword = request.GET.get("search", "").strip()
            for field in self.search_fields:
                query |= Q(**{"%s__icontains" % field: keyword})

            if issubclass(cls, Contact) or issubclass(cls, get_user_model()):
                query &= Q(is_active=True)

            qs = qs.filter(query)

        search_mode = request.GET.get("searchMode")
        if search_mode and search_mode == "main" and issubclass(cls, Product):
            qs = qs.filter(mode__in=[
                ProductMode.SIMPLE_VARIATION_PARENT,
                ProductMode.VARIABLE_VARIATION_PARENT,
                ProductMode.NORMAL
            ])

        if search_mode and search_mode == "sellable_mode_only" and issubclass(cls, Product):
            qs = qs.exclude(
                Q(mode__in=[ProductMode.SIMPLE_VARIATION_PARENT, ProductMode.VARIABLE_VARIATION_PARENT]) |
                Q(deleted=True) |
                Q(shop_products__visibility=ShopProductVisibility.NOT_VISIBLE)
            ).filter(shop_products__purchasable=True)

        sales_units = request.GET.get("salesUnits")
        if sales_units and issubclass(cls, Product):
            qs = qs.filter(sales_unit__translations__symbol__in=sales_units.strip().split(","))

        qs = qs.distinct()
        return [{"id": obj.id, "name": force_text(obj)} for obj in qs[:self.result_limit]]

    def _filter_query(self, cls, qs, shop, is_superuser):
        if hasattr(cls.objects, "all_except_deleted"):
            qs = cls.objects.all_except_deleted(shop=shop)
        if hasattr(cls.objects, "get_for_user"):
            qs = cls.objects.get_for_user(self.request.user)
        if issubclass(cls, Product):
            qs = qs.filter(shop_products__shop=shop)

        # filter by shop, when not superuser
        if not is_superuser:
            # Get all relation fields and check whether this models has
            # relation to Shop mode, if so, filter by the current shop
            allowed_shop_fields = ["shop", "shops"]
            related_fields = [models.OneToOneField, models.ForeignKey, models.ManyToManyField]
            shop_related_fields = [
                field
                for field in cls._meta.get_fields()
                if type(field) in related_fields and field.related_model == Shop and field.name in allowed_shop_fields
            ]
            for shop_field in shop_related_fields:
                qs = qs.filter(**{shop_field.name: shop})

        return qs

    def get(self, request, *args, **kwargs):
        return JsonResponse({"results": self.get_data(request, *args, **kwargs)})
