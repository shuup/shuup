# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Optional, Union

from shuup.core.models import AnonymousContact, Product, ProductCatalogPrice, ShopProduct, Supplier


def index_product(product: Union[Product, int], supplier: Optional[Union[Supplier, int]] = None):
    product_id = product if not isinstance(product, Product) else product.pk
    shop_products = ShopProduct.objects.filter(product_id=product_id)
    if supplier:
        shop_products = shop_products.filter(suppliers=supplier)
    for shop_product in shop_products:
        index_shop_product(shop_product=shop_product)


def update_shop_product_stocks(shop_product: Union[ShopProduct, int], supplier_id=None):
    from shuup.simple_supplier.module import SimpleSupplierModule

    if not isinstance(shop_product, ShopProduct):
        shop_product = ShopProduct.objects.select_related("product").get(pk=shop_product)

    suppliers = Supplier.objects.filter(
        shop_products=shop_product.pk, supplier_modules__module_identifier=SimpleSupplierModule.identifier
    ).distinct()
    if supplier_id:
        suppliers = suppliers.filter(pk=supplier_id)
    for supplier in suppliers:
        supplier.update_stock(product_id=shop_product.product_id)


def update_product_stocks(product: Union[Product, int], supplier_id=None):
    from shuup.simple_supplier.module import SimpleSupplierModule

    suppliers = Supplier.objects.filter(
        shop_products__product_id=product, supplier_modules__module_identifier=SimpleSupplierModule.identifier
    ).distinct()
    if supplier_id:
        suppliers = suppliers.filter(pk=supplier_id)
    for supplier in suppliers:
        supplier.update_stock(product_id=product)


def index_shop_product(shop_product: Union[ShopProduct, int]):
    # get all the suppliers that are linked to the shop product
    # that has the simple_supplier module
    from shuup.simple_supplier.module import SimpleSupplierModule

    if not isinstance(shop_product, ShopProduct):
        shop_product = ShopProduct.objects.select_related("product").get(pk=shop_product)

    suppliers = (
        Supplier.objects.filter(
            shop_products=shop_product.pk, supplier_modules__module_identifier=SimpleSupplierModule.identifier
        )
        .distinct()
        .only("pk", "module_data")
    )

    for supplier in suppliers:
        is_purchasable = not (
            list(
                shop_product.get_purchasability_errors(
                    supplier=supplier,
                    customer=AnonymousContact(),
                    quantity=shop_product.minimum_purchase_quantity,
                )
            )
        )
        ProductCatalogPrice.objects.filter(
            product_id=shop_product.product_id, shop_id=shop_product.shop_id, supplier_id=supplier.pk
        ).update(is_available=is_purchasable)

    if shop_product.product.is_variation_parent():
        # also index child products
        children_shop_product = ShopProduct.objects.filter(
            product__variation_parent_id=shop_product.product_id, shop_id=shop_product.shop_id
        )
        for child_shop_product in children_shop_product:
            index_shop_product(child_shop_product)
