# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField

from shoop.core.fields import InternalIdentifierField
from shoop.core.modules import ModuleInterface

from ._base import ShoopModel


class SupplierType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


@python_2_unicode_compatible
class Supplier(ModuleInterface, ShoopModel):
    default_module_spec = "shoop.core.suppliers:BaseSupplierModule"
    module_provides_key = "supplier_module"

    identifier = InternalIdentifierField(unique=True)
    name = models.CharField(verbose_name=_("name"), max_length=64)
    type = EnumIntegerField(SupplierType, verbose_name=_("supplier type"), default=SupplierType.INTERNAL)
    stock_managed = models.BooleanField(verbose_name=_("stock managed"), default=False)
    module_identifier = models.CharField(max_length=64, blank=True, verbose_name=_('module'))
    module_data = JSONField(blank=True, null=True, verbose_name=_("module data"))

    def __str__(self):
        return self.name

    def get_orderability_errors(self, shop_product, quantity, customer):
        """
        :param shop_product: Shop Product
        :type shop_product: shoop.core.models.ShopProduct
        :param quantity: Quantity to order
        :type quantity: decimal.Decimal
        :param contect: Ordering contact.
        :type contect: shoop.core.models.Contact
        :rtype: iterable[ValidationError]
        """
        return self.module.get_orderability_errors(shop_product=shop_product, quantity=quantity, customer=customer)

    def get_stock_statuses(self, product_ids):
        """
        :param product_ids: Iterable of product IDs
        :return: Dict of {product_id: ProductStockStatus}
        :rtype: dict[int, shoop.core.stocks.ProductStockStatus]
        """
        return self.module.get_stock_statuses(product_ids)

    def get_stock_status(self, product_id):
        """
        :param product_id: Product ID
        :type product_id: int
        :rtype: shoop.core.stocks.ProductStockStatus
        """
        return self.module.get_stock_status(product_id)

    def adjust_stock(self, product_id, delta, created_by=None):
        return self.module.adjust_stock(product_id, delta, created_by=created_by)

    def update_stock(self, product_id):
        return self.module.update_stock(product_id)

    def update_stocks(self, product_ids):
        return self.module.update_stocks(product_ids)
