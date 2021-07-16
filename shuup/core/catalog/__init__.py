# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import F, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from typing import Optional, Union

from shuup.core.catalog.signals import index_catalog_shop_product
from shuup.core.models import (
    Contact,
    Product,
    ProductCatalogAvailability,
    ProductCatalogPrice,
    Shop,
    ShopProduct,
    Supplier,
)


class ProductCatalogContext:
    """
    The catalog context object helps the catalog object
    to filter products according to the context's attributes.

    `shop` can be either a Shop instance or a shop id,
        used to filter the products for the given shop.

    `supplier` can be either a Supplier instance or a supplier id,
        used to filter the products for the given supplier.

    `user` can be either a User instance or a user id,
        used to filter the products for the given user.

    `contact` can be either a Contact instance or a contact id,
        used to filter the products for the given contact.

    `purchasable_only` filter the products that can be purchased.
    """

    def __init__(
        self,
        shop: Optional[Union[Shop, int]] = None,
        supplier: Optional[Union[Supplier, int]] = None,
        user: Optional[Union[AbstractUser, AnonymousUser, int]] = None,
        contact: Optional[Union[Contact, int]] = None,
        purchasable_only: bool = True,
    ):
        self.shop = shop
        self.supplier = supplier
        self.user = user
        self.contact = contact
        self.purchasable_only = purchasable_only


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
        filters = Q()
        shop = self.context.shop
        supplier = self.context.supplier
        contact = self.context.contact

        if shop:
            filters &= Q(shop=shop)
        if supplier:
            filters &= Q(supplier=supplier)

        if contact:
            # filter all prices for the contact OR to the groups of the contact
            filters = Q(Q(filters) & Q(Q(contact=contact) | Q(contact_group__members=contact)))

        product_prices = ProductCatalogPrice.objects.filter(product=OuterRef("pk")).filter(filters)

        products_qs = Product.objects.annotate(
            catalog_price=Subquery(product_prices.order_by("-price_value").values("price_value")[:1]),
            catalog_discounted_price=Subquery(
                product_prices.filter(discounted_price_value__isnull=False)
                .order_by("-discounted_price_value")
                .values("discounted_price_value")[:1]
            ),
        )

        if self.context.purchasable_only:
            availability_filter = Q(is_available=True)
            if shop:
                availability_filter &= Q(shop=shop)
            if supplier:
                availability_filter &= Q(supplier=supplier)

            products_qs = products_qs.filter(
                pk__in=ProductCatalogAvailability.objects.filter(availability_filter).values_list("product").distinct()
            )

        return products_qs

    def get_shop_products_queryset(self) -> "QuerySet[ShopProduct]":
        """
        Returns a queryset of ShopProduct annotated with price and discounted price:
        The catalog will filter the shop products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        filters = Q()
        shop = self.context.shop
        supplier = self.context.supplier
        contact = self.context.contact

        if shop:
            filters &= Q(shop=shop)
        if supplier:
            filters &= Q(supplier=supplier)

        if contact:
            # filter all prices for the contact OR to the groups of the contact
            filters = Q(Q(filters) & Q(Q(contact=contact) | Q(contact_group__members=contact)))

        product_prices = ProductCatalogPrice.objects.filter(product=OuterRef("product_id")).filter(filters)

        shop_products_qs = ShopProduct.objects.annotate(
            catalog_price=Coalesce(
                Subquery(product_prices.order_by("-price_value").values("price_value")[:1]),
                F("default_price_value"),
            ),
            catalog_discounted_price=Subquery(
                product_prices.filter(discounted_price_value__isnull=False)
                .order_by("-discounted_price_value")
                .values("discounted_price_value")[:1]
            ),
        )

        if self.context.purchasable_only:
            availability_filter = Q(is_available=True)
            if shop:
                availability_filter &= Q(shop=shop)
            if supplier:
                availability_filter &= Q(supplier=supplier)

            shop_products_qs = shop_products_qs.filter(
                product__in=ProductCatalogAvailability.objects.filter(availability_filter)
                .values_list("product")
                .distinct()
            )

        return shop_products_qs

    @classmethod
    def index_product(cls, product: Union[Product, int]):
        """
        Index the prices for the given `product`
        which can be either a Product instance or a product ID.
        """
        for shop_product in ShopProduct.objects.filter(product=product):
            cls.index_shop_product(shop_product)

    @classmethod
    def index_shop_product(cls, shop_product: Union[Product, int]):
        """
        Index the prices for the given `shop_product`
        which can be either a ShopProduct instance or a shop product ID.
        """
        if isinstance(shop_product, int):
            shop_product = ShopProduct.objects.get(pk=shop_product).only("shop_id", "product_id", "default_price_value")

        # save the default product price
        ProductCatalogPrice.objects.update_or_create(
            product_id=shop_product.product_id,
            shop_id=shop_product.shop_id,
            defaults=dict(price_value=shop_product.default_price_value),
        )

        index_catalog_shop_product.send(sender=cls, shop_product=shop_product)
