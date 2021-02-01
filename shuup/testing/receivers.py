# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import (
    AnonymousContact, ShopProduct, ShopProductVisibility
)


def shop_product_orderability_check(sender, **kwargs):
    """
    Signal handler for detecting shop product orderability changes

    For projects which purchasable doesn't change based on contact
    or contact group can hide unorderable products from frontend
    by changing the product visibility. By default Shuup shows all
    visible products at front which might not be desired for all
    projects.

    Orderability can depend on contact or contact group only when
    some custom supplier modules are included. In these cases
    the project orderability signal handler has to adapt accordingly.
    """
    for shop in kwargs["shops"]:
        for shop_product in ShopProduct.objects.filter(
                shop=shop, product_id__in=kwargs["product_ids"]).exclude(visibility=ShopProductVisibility.NOT_VISIBLE):
            ensure_shop_product_visibility(shop_product)


def ensure_shop_product_visibility(shop_product):
    if shop_product.visibility == ShopProductVisibility.NOT_VISIBLE:
        # Already hidden shop products can be skipped
        return

    purchasable = False
    for supplier in shop_product.suppliers.enabled():
        if purchasable:
            break

        if shop_product.is_purchasable(
                supplier=supplier, customer=AnonymousContact(), quantity=shop_product.minimum_purchase_quantity):
            # Product is purchasable for at least one supplier so we can
            # quit the purchasability checks for this product
            purchasable = True
            continue

    # Product not purchasable for any supplier means it can not be
    # orderable so we might as well hide the product since
    # we do not want to show unorderable products at front.
    if not purchasable:
        shop_product.visibility = ShopProductVisibility.NOT_VISIBLE
        shop_product.save()
