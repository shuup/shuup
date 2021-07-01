# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models.query import QuerySet
from typing import Optional, Union

from shuup.core.models import Contact, Product, Shop, ShopProduct, Supplier


class ProductCatalogContext:
    def __init__(
        self,
        shop: Optional[Shop] = None,
        supplier: Optional[Supplier] = None,
        user: Optional[Union[AbstractUser, AnonymousUser]] = None,
        contact: Optional[Contact] = None,
        orderable_only: bool = True,
    ):
        self.shop = shop
        self.supplier = supplier
        self.user = user
        self.contact = contact
        self.orderable_only = orderable_only


class ProductCatalog:
    """
    A helper class to return products and shop products from the database
    """

    def __init__(self, context: Optional[ProductCatalogContext] = None):
        self.context = context or ProductCatalogContext()

    def get_products_queryset(self) -> "QuerySet[Product]":
        """
        Returns a queryset of Product annotated with price and discounted price:
        The catalog will filter the products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        return Product.objects.all()

    def get_shop_products_queryset(self) -> "QuerySet[ShopProduct]":
        """
        Returns a queryset of ShopProduct annotated with price and discounted price:
        The catalog will filter the shop products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        return Product.objects.all()
