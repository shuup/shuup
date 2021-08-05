# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from functools import lru_cache
from typing import TYPE_CHECKING, Dict, Iterable, Optional

from shuup.apps.provides import get_provide_objects
from shuup.core.specs.product_kind import ProductKindSpec
from shuup.core.stocks import ProductStockStatus

from .enums import StockAdjustmentType

USER_MODEL = get_user_model()

if TYPE_CHECKING:  # pragma: no cover
    from shuup.core.models import Contact, Product, Shipment, ShopProduct, Supplier


@lru_cache()
def get_supported_product_kinds_for_module(module_identifier: str) -> Iterable[ProductKindSpec]:
    specs = []
    for product_kind_spec in get_provide_objects("product_kind_specs"):
        supported_modules = product_kind_spec.supported_supplier_modules
        if not supported_modules or module_identifier in supported_modules:
            specs.append(product_kind_spec)
    return specs


@lru_cache()
def get_supported_product_kinds_values_for_module(module_identifier: str) -> Iterable[int]:
    return list([spec.value for spec in get_supported_product_kinds_for_module(module_identifier)])


class SupplierModuleInterface:
    """
    Supplier module interface.
    """

    identifier = None  # type: str
    name = None  # type: str

    def get_stock_statuses(self, product_ids, *args, **kwargs) -> Dict[int, ProductStockStatus]:
        """
        :param product_ids: Iterable of product IDs.
        :return: Dict of {product_id: ProductStockStatus}.
        """
        return {}

    def get_stock_status(self, product_id: int, *args, **kwargs) -> Optional[ProductStockStatus]:
        """
        :param product_id: Product ID.
        :type product_id: int
        :rtype: shuup.core.stocks.ProductStockStatus|None
        """
        return None

    def get_orderability_errors(
        self, shop_product: "ShopProduct", quantity: Decimal, customer: "Contact"
    ) -> Iterable[ValidationError]:
        """
        :param shop_product: Shop Product.
        :type shop_product: shuup.core.models.ShopProduct
        :param quantity: Quantity to order.
        :type quantity: decimal.Decimal
        :param customer: Contact.
        """
        return []

    def adjust_stock(
        self,
        product_id: int,
        delta: Decimal,
        created_by: USER_MODEL = None,
        type: StockAdjustmentType = StockAdjustmentType.INVENTORY,
        *args,
        **kwargs
    ) -> None:
        """
        Adjusts the stock for the given `product_id`.
        """
        pass

    def update_stock(self, product_id: int, *args, **kwargs) -> None:
        """
        Updates a stock for the given `product_id`
        """
        pass

    def update_stocks(self, product_ids: Iterable[int], *args, **kwargs) -> None:
        pass

    def ship_products(self, shipment: "Shipment", product_quantities: Dict["Product", Decimal], *args, **kwargs):
        pass

    @classmethod
    def get_supported_product_kinds(cls) -> Iterable[ProductKindSpec]:
        raise NotImplementedError

    @classmethod
    def get_supported_product_kinds_values(cls) -> Iterable[int]:
        raise NotImplementedError


class BaseSupplierModule(SupplierModuleInterface):
    """
    Base supplier module implementation.
    """

    def __init__(self, supplier: "Supplier", options: Dict):
        """
        :type supplier: Supplier.
        :type options: dict
        """
        self.supplier = supplier
        self.options = options

    @classmethod
    def get_supported_product_kinds(cls) -> Iterable[ProductKindSpec]:
        return get_supported_product_kinds_for_module(cls.identifier)

    @classmethod
    def get_supported_product_kinds_values(cls) -> Iterable[int]:
        return get_supported_product_kinds_values_for_module(cls.identifier)

    def get_stock_status(self, product_id: int, *args, **kwargs):
        statuses = self.get_stock_statuses([product_id])
        if product_id in statuses:
            return statuses[product_id]

    def update_stocks(self, product_ids: Iterable[int], *args, **kwargs):
        # Naive default implementation; smarter modules can do something better
        for product_id in product_ids:
            self.update_stock(product_id)
