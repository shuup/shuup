# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import OuterRef, Q, Subquery
from django.db.models.query import QuerySet
from django.utils import timezone
from typing import Optional, Union

from shuup.core.catalog.signals import index_catalog_shop_product
from shuup.core.models import (
    AnonymousContact,
    Contact,
    Product,
    ProductCatalogDiscountedPrice,
    ProductCatalogDiscountedPriceRule,
    ProductCatalogPrice,
    ProductCatalogPriceRule,
    ProductVisibility,
    Shop,
    ShopProduct,
    ShopProductVisibility,
    Supplier,
    SupplierShop,
)
from shuup.core.pricing import get_discount_modules, get_pricing_module
from shuup.core.utils.users import is_user_all_seeing


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

    `contact` a Contact instance used to filter the products for the given contact.

    `visible_only` filter the products that are visible.
        Deleted products and with visibility limitations
        will be removed from the list.

    `visibility` the shop product visibility. If set to None, all
        products for any visibility will be returned.
        if `purchasable_only` is True, this will be ignored.

    `purchasable_only` filter the products that can be purchased.
        This will make `visible_only` to be True.
    """

    def __init__(
        self,
        shop: Optional[Union[Shop, int]] = None,
        supplier: Optional[Union[Supplier, int]] = None,
        user: Optional[Union[AbstractUser, AnonymousUser, int]] = None,
        contact: Optional[Contact] = None,
        visible_only: bool = True,
        visibility: Optional[ShopProductVisibility] = None,
        purchasable_only: bool = True,
    ):
        self.shop = shop
        self.supplier = supplier
        self.user = user
        self.contact = contact
        self.visible_only = True if purchasable_only else visible_only
        self.purchasable_only = purchasable_only
        self.visibility = visibility


def get_contact_filter(contact: Optional[Contact]):
    if contact:
        # filter all prices for the contact OR to the groups of the contact
        return Q(
            Q(contact=contact)
            # evaluate contact group to prevent doing expensive joins on db
            | Q(contact_group_id__in=list(contact.groups.values_list("pk", flat=True)))
            | Q(contact_group__isnull=True, contact__isnull=True)
        )
    # anonymous contact
    return Q(
        Q(contact_group__isnull=True, contact__isnull=True)
        | Q(contact_group_id=AnonymousContact.get_default_group().pk)
    )


class ProductCatalog:
    """
    A helper class to return products and shop products from the database
    """

    def __init__(self, context: Optional[ProductCatalogContext] = None):
        self.context = context or ProductCatalogContext()

    def _get_prices_filters(self):
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

        filters &= Q(
            Q(catalog_rule__isnull=True)
            | Q(catalog_rule__in=ProductCatalogPriceRule.objects.filter(get_contact_filter(contact)))
        )

        return filters

    def _get_discounted_prices_filters(self):
        now_dt = timezone.localtime(timezone.now())
        now_time = now_dt.time()

        filters = Q()
        shop = self.context.shop
        supplier = self.context.supplier

        if shop:
            filters &= Q(shop=shop)
        if supplier:
            filters &= Q(supplier=supplier)

        filters &= Q(
            catalog_rule__in=ProductCatalogDiscountedPriceRule.objects.filter(
                Q(get_contact_filter(self.context.contact)),
                Q(
                    Q(
                        valid_start_date__isnull=True,
                        valid_start_hour__isnull=True,
                    )
                    | Q(
                        valid_start_date__lte=now_dt,
                        valid_end_date__gt=now_dt,
                        valid_start_hour__isnull=True,
                    )
                    | Q(
                        valid_start_date__lte=now_dt,
                        valid_end_date__gt=now_dt,
                        valid_start_hour__lte=now_time,
                        valid_end_hour__gt=now_time,
                        valid_weekday__isnull=True,
                    )
                    | Q(
                        valid_start_date__lte=now_dt,
                        valid_end_date__gt=now_dt,
                        valid_start_hour__lte=now_time,
                        valid_end_hour__gt=now_time,
                        valid_weekday=now_dt.weekday(),
                    ),
                ),
            )
        )
        return filters

    def annotate_products_queryset(
        self, queryset: "QuerySet[Product]", annotate_discounts: bool = True
    ) -> "QuerySet[Product]":
        """
        Returns the given Product queryset annotated with price and discounted price.
        The catalog will filter the products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        product_prices = (
            ProductCatalogPrice.objects.filter(product=OuterRef("pk"))
            .filter(self._get_prices_filters())
            .order_by("price_value")
        )

        # only visible products, we need to filter those through queryset
        if self.context.visible_only:
            visible_shop_products = self.filter_visible_shop_products(ShopProduct.objects.all())
            queryset = queryset.filter(
                pk__in=visible_shop_products.values_list("product_id", flat=True), deleted=False
            ).distinct()

        queryset = queryset.annotate(
            catalog_price=Subquery(product_prices.values("price_value")[:1]),
        )

        if annotate_discounts:
            product_discounted_prices = (
                ProductCatalogDiscountedPrice.objects.filter(product=OuterRef("pk"))
                .filter(self._get_discounted_prices_filters())
                .order_by("discounted_price_value")
            )
            queryset = queryset.annotate(
                catalog_discounted_price=Subquery(product_discounted_prices.values("discounted_price_value")[:1]),
            )
        return queryset

    def filter_visible_shop_products(self, queryset: "QuerySet[ShopProduct]") -> "QuerySet[ShopProduct]":
        """
        Filter visible shop products according to the context
        """
        contact = self.context.contact

        user = self.context.user
        if not user and self.context.contact and hasattr(self.context.contact, "user"):
            user = self.context.contact.user

        user_all_seeing = is_user_all_seeing(user) if user else False

        # user can see all shop products
        if user_all_seeing:
            return queryset

        shop_product_filters = Q(Q(available_until__isnull=True) | Q(available_until__gte=timezone.now()))

        visible_suppliers = SupplierShop.objects.filter(supplier__enabled=True, is_approved=True)
        if self.context.shop:
            shop_product_filters &= Q(shop=self.context.shop)
            visible_suppliers = visible_suppliers.filter(shop=self.context.shop)
        if self.context.supplier:
            visible_suppliers = visible_suppliers.filter(supplier=self.context.supplier)

        shop_product_filters &= Q(suppliers__in=visible_suppliers.values_list("supplier", flat=True))

        if contact:
            shop_product_filters &= Q(
                Q(visibility_limit__in=(ProductVisibility.VISIBLE_TO_ALL, ProductVisibility.VISIBLE_TO_LOGGED_IN))
                | Q(visibility_limit=ProductVisibility.VISIBLE_TO_GROUPS, visibility_groups__in=contact.groups.all())
            )
        else:
            shop_product_filters &= Q(
                Q(visibility_limit=ProductVisibility.VISIBLE_TO_ALL)
                | Q(
                    visibility_limit=ProductVisibility.VISIBLE_TO_GROUPS,
                    visibility_groups=AnonymousContact.get_default_group(),
                )
            )

        if self.context.visibility:
            if self.context.visibility not in (ShopProductVisibility.NOT_VISIBLE, ShopProductVisibility.ALWAYS_VISIBLE):
                shop_product_filters &= Q(
                    visibility__in=[self.context.visibility, ShopProductVisibility.ALWAYS_VISIBLE]
                )
        else:
            shop_product_filters &= Q(visibility=ShopProductVisibility.ALWAYS_VISIBLE)

        return queryset.filter(shop_product_filters).distinct()

    def get_products_queryset(self, annotate_discounts=True) -> "QuerySet[Product]":
        """
        Returns a queryset of Product annotated with price and discounted price:
        The catalog will filter the products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        return self.annotate_products_queryset(Product.objects.all(), annotate_discounts=annotate_discounts).filter(
            catalog_price__isnull=False
        )

    def annotate_shop_products_queryset(
        self, queryset: "QuerySet[ShopProduct]", annotate_discounts: bool = True
    ) -> "QuerySet[ShopProduct]":
        """
        Returns a the given ShopProduct queryset annotated with price and discounted price:
        The catalog will filter the shop products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        product_prices = (
            ProductCatalogPrice.objects.filter(product=OuterRef("product_id"))
            .filter(self._get_prices_filters())
            .order_by("price_value")
        )

        if self.context.visible_only:
            queryset = self.filter_visible_shop_products(queryset).filter(product__deleted=False)

        queryset = queryset.annotate(
            # as we are filtering ShopProducts, we can fallback to default_price_value
            # when the product is a variation parent (this is not possible with product queryset)
            catalog_price=Subquery(product_prices.values("price_value")[:1]),
        )
        if annotate_discounts:
            product_discounted_prices = (
                ProductCatalogDiscountedPrice.objects.filter(product=OuterRef("product_id"))
                .filter(self._get_discounted_prices_filters())
                .order_by("discounted_price_value")
            )
            queryset = queryset.annotate(
                catalog_discounted_price=Subquery(product_discounted_prices.values("discounted_price_value")[:1]),
            )

        return queryset

    def get_shop_products_queryset(self, annotate_discounts=True) -> "QuerySet[ShopProduct]":
        """
        Returns a queryset of ShopProduct annotated with price and discounted price:
        The catalog will filter the shop products according to the `context`.

            - `catalog_price` -> the cheapest price found for the context
            - `catalog_discounted_price` -> the cheapest discounted price found for the context
        """
        return self.annotate_shop_products_queryset(
            ShopProduct.objects.all(), annotate_discounts=annotate_discounts
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
    def index_shop_product(cls, shop_product: Union[Product, int], **kwargs):
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
