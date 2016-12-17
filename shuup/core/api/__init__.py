# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.api.factories import viewset_factory
from shuup.core.api.attribute import AttributeViewSet
from shuup.core.api.contacts import ContactViewSet
from shuup.core.api.manufacturer import ManufacturerViewSet
from shuup.core.api.orders import OrderViewSet
from shuup.core.api.product_media import ProductMediaViewSet
from shuup.core.api.products import (
    ProductAttributeViewSet, ProductPackageViewSet, ProductTypeViewSet,
    ProductViewSet, ShopProductViewSet
)
from shuup.core.api.shipments import ShipmentViewSet
from shuup.core.api.suppliers import SupplierViewSet
from shuup.core.api.tax_class import TaxClassViewSet
from shuup.core.api.units import SalesUnitViewSet
from shuup.core.api.users import UserViewSet
from shuup.core.models import Category, Shop


def populate_core_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/attribute", AttributeViewSet)
    router.register("shuup/category", viewset_factory(Category))
    router.register("shuup/contact", ContactViewSet)
    router.register("shuup/order", OrderViewSet)
    router.register("shuup/product", ProductViewSet)
    router.register("shuup/product_attribute", ProductAttributeViewSet)
    router.register("shuup/product_media", ProductMediaViewSet)
    router.register("shuup/product_type", ProductTypeViewSet)
    router.register("shuup/product_package", ProductPackageViewSet)
    router.register("shuup/shipment", ShipmentViewSet)
    router.register("shuup/shop", viewset_factory(Shop))
    router.register("shuup/shop_product", ShopProductViewSet)
    router.register("shuup/manufacturer", ManufacturerViewSet)
    router.register("shuup/supplier", SupplierViewSet)
    router.register("shuup/user", UserViewSet)
    router.register("shuup/sales_unit", SalesUnitViewSet)
    router.register("shuup/tax_class", TaxClassViewSet)
