# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import Case, F, OuterRef, Q, Subquery, When
from django.db.models.query import QuerySet
from typing import Optional, Union

from shuup.core.catalog.signals import index_catalog_shop_product
from shuup.core.models import (
    AnonymousContact,
    Contact,
    Product,
    ProductCatalogPrice,
    ProductMode,
    Shop,
    ShopProduct,
    Supplier,
)
from shuup.core.pricing import get_discount_modules, get_pricing_module


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

    def _get_common_filters(self):
        filters = Q()
        shop = self.context.shop
        supplier = self.context.supplier
        contact = self.context.contact
        purchasable_only = self.context.purchasable_only

        if shop:
            filters &= Q(shop=shop)
        if supplier:
            filters &= Q(supplier=supplier)
        if purchasable_only:
            filters &= Q(is_available=True)

        if contact:
            # filter all prices for the contact OR to the groups of the contact
            filters = Q(
                Q(filters)
                & Q(
                    Q(contact=contact)
                    | Q(contact_group__in=contact.groups.values_list("pk", flat=True))
                    | Q(contact_group__isnull=True, contact__isnull=True)
                )
            )
        else:
            # anonymous contact
            filters = Q(
                Q(filters)
                & Q(
                    Q(contact_group__isnull=True, contact__isnull=True)
                    | Q(contact_group=AnonymousContact.get_default_group())
                )
            )

        return filters

    def get_products_queryset(self) -> "QuerySet[Product]":
        """
        Returns a queryset of Product annotated with price and discounted price:
        The catalog will filter the products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        filters = self._get_common_filters()

        product_prices = (
            ProductCatalogPrice.objects.filter(product=OuterRef("pk")).filter(filters).order_by("price_value")
        )

        return Product.objects.annotate(
            catalog_price=Subquery(product_prices.values("price_value")[:1]),
            catalog_discounted_price=Subquery(product_prices.values("discounted_price_value")[:1]),
        ).filter(catalog_price__isnull=False)

    def get_shop_products_queryset(self) -> "QuerySet[ShopProduct]":
        """
        Returns a queryset of ShopProduct annotated with price and discounted price:
        The catalog will filter the shop products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        filters = self._get_common_filters()

        product_prices = (
            ProductCatalogPrice.objects.filter(product=OuterRef("product_id")).filter(filters).order_by("price_value")
        )

        return ShopProduct.objects.annotate(
            # as we are filtering ShopProducts, we can fallback to default_price_value
            # when the product is a variation parent (this is not possible with product queryset)
            catalog_price=Case(
                When(
                    product__mode__in=[
                        ProductMode.VARIABLE_VARIATION_PARENT,
                        ProductMode.SIMPLE_VARIATION_PARENT,
                    ],
                    then=F("default_price_value"),
                ),
                default=Subquery(product_prices.values("price_value")[:1]),
            ),
            catalog_discounted_price=Subquery(product_prices.values("discounted_price_value")[:1]),
        ).filter(catalog_price__isnull=False)

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

        This method will forward the indexing for the default pricing module
        and then trigger a signal for other apps to do their job if they need.
        """
        pricing_module = get_pricing_module()
        pricing_module.index_shop_product(shop_product)
        for discount_module in get_discount_modules():
            discount_module.index_shop_product(shop_product)
        index_catalog_shop_product.send(sender=cls, shop_product=shop_product)
