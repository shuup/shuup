# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import ShopProduct, Supplier
from shuup.utils.django_compat import force_text
from shuup.utils.excs import Problem


class SupplierModuleInterface(object):
    """
    Supplier module interface.
    """

    identifier = None
    name = None
    handles_internal_types = []

    def __init__(self, supplier, options):
        pass

    def get_can_handel_product_ids(self, product_ids):
        return []

    def can_handel_product_id(self, product_id):
        return False

    def get_can_handel_shop_product_ids(self, shop_product_ids):
        return []

    def can_handel_shop_product_id(self, shop_product_id):
        return False

    def get_stock_statuses(self, product_ids):
        return {}

    def get_stock_status(self, product_id):
        pass

    def get_orderability_errors(self, shop_product, quantity, customer):
        pass

    def adjust_stock(self, product_id, delta, created_by=None, type=None):
        pass

    def update_stock(self, product_id):
        pass

    def update_stocks(self, product_ids):
        pass

    def ship_products(self, shipment, product_quantities):
        pass


class BaseSupplierModule(SupplierModuleInterface):
    """
    Base supplier module implementation.
    """

    def __init__(self, supplier, options):
        """
        :type supplier: Supplier.
        :type options: dict
        """
        self.supplier = supplier
        self.options = options

    def _get_can_handle_product_queryset(self, ids):
        from shuup.core.models import Product

        return Product.objects.filter(id__in=ids, internal_type__in=self.handles_internal_types)

    def _get_can_handle_shop_product_queryset(self, ids):
        return ShopProduct.objects.filter(id__in=ids, product__internal_type__in=self.handles_internal_types)

    def get_can_handel_product_ids(self, product_ids):
        """
        :param product_ids: Product IDs.
        :type product_ids: iterable[int]
        :return: list of all product ids that this module can handle
        :rtype: iterable[int]
        """
        if not self.handles_internal_types:
            return True

        return self._get_can_handle_product_queryset(product_ids).values_list("id", flat=True)

    def can_handel_product_id(self, product_id):
        """
        :param product_ids: Product ID.
        :type product_ids: int
        :return: returns true if this module can handle the product
        :rtype: bool
        """
        if not self.handles_internal_types:
            return True

        return self._get_can_handle_product_queryset([product_id]).exists()

    def get_can_handel_shop_product_ids(self, shop_product_ids):
        """
        :param product_ids: Shop Product IDs.
        :type product_ids: iterable[int]
        :return: list of all shop product ids that this module can handle
        :rtype: iterable[int]
        """
        if not self.handles_internal_types:
            return True

        return self._get_can_handle_shop_product_queryset(shop_product_ids).values_list("id", flat=True)

    def can_handel_shop_product_id(self, shop_product_id):
        """
        :param product_ids: Shop Product ID
        :type product_ids: int
        :return: returns true if this module can handle the product
        :rtype: bool
        """
        if not self.handles_internal_types:
            return True

        return self._get_can_handle_shop_product_queryset([shop_product_id]).exists()

    def get_stock_statuses(self, product_ids):
        """
        :param product_ids: Iterable of product IDs.
        :return: Dict of {product_id: ProductStockStatus}.
        :rtype: dict[int, shuup.core.stocks.ProductStockStatus]
        """
        return {}

    def get_stock_status(self, product_id):
        """
        :param product_id: Product ID.
        :type product_id: int
        :rtype: shuup.core.stocks.ProductStockStatus
        """
        statuses = self.get_stock_statuses([product_id])
        if product_id in statuses:
            return statuses[product_id]
        return

    def get_orderability_errors(self, shop_product, quantity, customer):
        """
        :param shop_product: Shop Product.
        :type shop_product: shuup.core.models.ShopProduct
        :param quantity: Quantity to order.
        :type quantity: decimal.Decimal
        :param customer: Contact.
        :type user: django.contrib.auth.models.AbstractUser
        :rtype: iterable[ValidationError]
        """
        vendor_user = None
        if hasattr(customer, "user"):
            vendor_user = customer.user.vendor_users.filter(
                supplier__in=Supplier.objects.enabled(shop=shop_product.shop), shop=shop_product.shop
            ).first()
        if vendor_user:
            yield ValidationError(
                _(
                    "Error! Your vendor can't handle this product type. "
                    "Please be in contact with your marketplace admin"
                ),
                code="missing_supplier_module",
            )
        else:
            yield ValidationError(
                _("Unfortunately product: %s can't be ordered right now.") % (shop_product.product.name,),
                code="missing_supplier_module",
            )

    def update_stocks(self, product_ids):
        # Naive default implementation; smarter modules can do something better
        for product_id in product_ids:
            self.update_stock(product_id)

    def ship_products(self, shipment, product_quantities):
        # stocks are managed, do stocks check
        if self.supplier.stock_managed:
            insufficient_stocks = {}

            for product, quantity in product_quantities.items():
                if quantity > 0:
                    stock_status = self.get_stock_status(product.pk)
                    if stock_status.stock_managed and stock_status.physical_count < quantity:
                        insufficient_stocks[product] = stock_status.physical_count

            if insufficient_stocks:
                formatted_counts = [
                    _("%(name)s (physical stock: %(quantity)s)")
                    % {"name": force_text(name), "quantity": force_text(quantity)}
                    for (name, quantity) in insufficient_stocks.items()
                ]
                raise Problem(
                    _("Insufficient physical stock count for the following products: `%(product_counts)s`.")
                    % {"product_counts": ", ".join(formatted_counts)}
                )

        for product, quantity in product_quantities.items():
            if quantity == 0:
                continue

            sp = shipment.products.create(product=product, quantity=quantity)
            sp.cache_values()
            sp.save()

        shipment.cache_values()
        shipment.save()
