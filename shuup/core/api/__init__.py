# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.api.address import MutableAddressViewSet
from shuup.core.api.attribute import AttributeViewSet
from shuup.core.api.basket import BasketViewSet
from shuup.core.api.category import CategoryViewSet
from shuup.core.api.contacts import ContactViewSet, PersonContactViewSet
from shuup.core.api.front_orders import FrontOrderViewSet
from shuup.core.api.front_passwords import (
    PasswordResetViewSet, SetPasswordViewSet
)
from shuup.core.api.front_products import (
    FrontProductViewSet, FrontShopProductViewSet
)
from shuup.core.api.front_users import FrontUserViewSet
from shuup.core.api.manufacturer import ManufacturerViewSet
from shuup.core.api.orders import OrderViewSet
from shuup.core.api.product_media import ProductMediaViewSet
from shuup.core.api.product_variation import (
    ProductVariationVariableValueViewSet, ProductVariationVariableViewSet
)
from shuup.core.api.products import (
    ProductAttributeViewSet, ProductPackageViewSet, ProductTypeViewSet,
    ProductViewSet, ShopProductViewSet
)
from shuup.core.api.shipments import ShipmentViewSet
from shuup.core.api.shop import ShopViewSet
from shuup.core.api.suppliers import SupplierViewSet
from shuup.core.api.tax import TaxViewSet
from shuup.core.api.tax_class import TaxClassViewSet
from shuup.core.api.units import SalesUnitViewSet
from shuup.core.api.users import UserViewSet


def populate_core_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/address", MutableAddressViewSet)
    router.register("shuup/attribute", AttributeViewSet)
    router.register("shuup/category", CategoryViewSet)
    router.register("shuup/contact", ContactViewSet)
    router.register("shuup/order", OrderViewSet)
    router.register("shuup/person_contact", PersonContactViewSet)
    router.register("shuup/product", ProductViewSet)
    router.register("shuup/product_attribute", ProductAttributeViewSet)
    router.register("shuup/product_media", ProductMediaViewSet)
    router.register("shuup/product_type", ProductTypeViewSet)
    router.register("shuup/product_package", ProductPackageViewSet)
    router.register("shuup/product_variation_variable", ProductVariationVariableViewSet)
    router.register("shuup/product_variation_variable_value", ProductVariationVariableValueViewSet)
    router.register("shuup/shipment", ShipmentViewSet)
    router.register("shuup/shop", ShopViewSet)
    router.register("shuup/shop_product", ShopProductViewSet)
    router.register("shuup/manufacturer", ManufacturerViewSet)
    router.register("shuup/supplier", SupplierViewSet)
    router.register("shuup/user", UserViewSet)
    router.register("shuup/sales_unit", SalesUnitViewSet)
    router.register("shuup/tax", TaxViewSet)
    router.register("shuup/tax_class", TaxClassViewSet)
    router.register("shuup/basket", BasketViewSet)

    router.register("shuup/front/user", FrontUserViewSet)
    router.register("shuup/front/password", SetPasswordViewSet, 'set_password')
    router.register("shuup/front/password/reset", PasswordResetViewSet, 'password_reset')
    router.register("shuup/front/orders", FrontOrderViewSet)
    router.register("shuup/front/shop_products", FrontShopProductViewSet)
    router.register("shuup/front/products", FrontProductViewSet)
