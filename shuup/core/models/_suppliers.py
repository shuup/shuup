# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from jsonfield import JSONField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedFields
from typing import TYPE_CHECKING, Union

from shuup.core.excs import SupplierHasNoSupplierModules
from shuup.core.fields import InternalIdentifierField
from shuup.core.modules import ModuleInterface
from shuup.utils.analog import define_log_model

from ._base import TranslatableShuupModel

if TYPE_CHECKING:  # pragma: no cover
    from shuup.core.models import Shop


LOGGER = logging.getLogger(__name__)


class SupplierType(Enum):
    INTERNAL = 1
    EXTERNAL = 2

    class Labels:
        INTERNAL = _("internal")
        EXTERNAL = _("external")


class SupplierQueryset(TranslatableQuerySet):
    def not_deleted(self):
        return self.filter(deleted=False)

    def enabled(self, shop: Union["Shop", int] = None):
        """
        Filter the queryset to contain only enabled and approved suppliers.

        If `shop` is given, only approved suppliers
        for the given shop will be filtered.

        `shop` can be either a Shop instance or the shop's PK
        """
        queryset = self.filter(enabled=True, supplier_shops__is_approved=True).not_deleted()

        if shop:
            from shuup.core.models import Shop

            shop_id = shop.pk if isinstance(shop, Shop) else shop
            queryset = queryset.filter(supplier_shops__shop_id=shop_id)

        return queryset.distinct()


@python_2_unicode_compatible
class Supplier(ModuleInterface, TranslatableShuupModel):
    module_provides_key = "supplier_module"

    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_("modified on"))
    identifier = InternalIdentifierField(unique=True)
    name = models.CharField(
        verbose_name=_("name"),
        max_length=128,
        db_index=True,
        help_text=_(
            "The product supplier's name. " "You can enable suppliers to manage the inventory of stocked products."
        ),
    )
    type = EnumIntegerField(
        SupplierType,
        verbose_name=_("supplier type"),
        default=SupplierType.INTERNAL,
        help_text=_(
            "The supplier type indicates whether the products are supplied through an internal supplier or "
            "an external supplier, and which group this supplier belongs to."
        ),
    )
    stock_managed = models.BooleanField(
        verbose_name=_("stock managed"),
        default=False,
        help_text=_(
            "Enable this if this supplier will manage the inventory of the stocked products. Having a managed stock "
            "enabled is unnecessary if e.g. selling digital products that will never run out no matter how many are "
            "being sold. There are some other cases when it could be an unnecessary complication. This setting"
            "merely assigns a sensible default behavior, which can be overwritten on a product-by-product basis."
        ),
    )
    supplier_modules = models.ManyToManyField(
        "SupplierModule",
        blank=True,
        related_name="suppliers",
        verbose_name=_("supplier modules"),
        help_text=_(
            "Select the supplier module to use for this supplier. "
            "Supplier modules define the rules by which inventory is managed."
        ),
    )
    module_data = JSONField(blank=True, null=True, verbose_name=_("module data"))

    shops = models.ManyToManyField(
        "Shop",
        blank=True,
        related_name="suppliers",
        verbose_name=_("shops"),
        help_text=_("You can select which particular shops fronts the supplier should be available in."),
        through="SupplierShop",
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("enabled"),
        help_text=_(
            "Indicates whether this supplier is currently enabled. In order to participate fully, "
            "the supplier also needs to be `Approved`."
        ),
    )
    logo = FilerImageField(
        verbose_name=_("logo"), blank=True, null=True, on_delete=models.SET_NULL, related_name="supplier_logos"
    )
    contact_address = models.ForeignKey(
        "MutableAddress",
        related_name="supplier_addresses",
        verbose_name=_("contact address"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    options = JSONField(blank=True, null=True, verbose_name=_("options"))
    translations = TranslatedFields(description=models.TextField(blank=True, verbose_name=_("description")))
    slug = models.SlugField(
        verbose_name=_("slug"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_(
            "Enter a URL slug for your supplier. Slug is user- and search engine-friendly short text "
            "used in a URL to identify and describe a resource. In this case it will determine "
            "what your supplier page URL in the browser address bar will look like. "
            "A default will be created using the supplier name."
        ),
    )
    deleted = models.BooleanField(default=False, verbose_name=_("deleted"))

    search_fields = ["name"]
    objects = SupplierQueryset.as_manager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Supplier, self).save(*args, **kwargs)

    def get_orderability_errors(self, shop_product, quantity, customer, *args, **kwargs):
        """
        :param shop_product: Shop Product.
        :type shop_product: shuup.core.models.ShopProduct
        :param quantity: Quantity to order.
        :type quantity: decimal.Decimal
        :param contect: Ordering contact.
        :type contect: shuup.core.models.Contact
        :rtype: iterable[ValidationError]
        """
        for module in self.modules:
            yield from module.get_orderability_errors(
                shop_product=shop_product, quantity=quantity, customer=customer, *args, **kwargs
            )

    def get_stock_statuses(self, product_ids, *args, **kwargs):
        """
        Return a dict of product stock statuses

        :param product_ids: Iterable of product IDs.
        :return: Dict of {product_id: ProductStockStatus}
        :rtype: dict[int, shuup.core.stocks.ProductStockStatus]
        """
        return_dict = {}
        for module in self.modules:
            return_dict.update(module.get_stock_statuses(product_ids, *args, **kwargs))
        return return_dict

    def get_stock_status(self, product_id, *args, **kwargs):
        for module in self.modules:
            stock_status = module.get_stock_status(product_id, *args, **kwargs)
            if stock_status.handled:
                return stock_status

    def get_suppliable_products(self, shop, customer):
        """
        :param shop: Shop to check for suppliability.
        :type shop: shuup.core.models.Shop
        :param customer: Customer contact to check for suppliability.
        :type customer: shuup.core.models.Contact
        :rtype: list[int]
        """
        return [
            shop_product.pk
            for shop_product in self.shop_products.filter(shop=shop)
            if shop_product.is_orderable(self, customer, shop_product.minimum_purchase_quantity)
        ]

    def adjust_stock(self, product_id, delta, created_by=None, type=None, *args, **kwargs):
        from shuup.core.suppliers.base import StockAdjustmentType

        adjustment_type = type or StockAdjustmentType.INVENTORY
        for module in self.modules:
            stock = module.adjust_stock(product_id, delta, created_by=created_by, type=adjustment_type, *args, **kwargs)
            if stock:
                return stock

    def update_stock(self, product_id, *args, **kwargs):
        for module in self.modules:
            module.update_stock(product_id, *args, **kwargs)

    def update_stocks(self, product_ids, *args, **kwargs):
        for module in self.modules:
            module.update_stocks(product_ids, *args, **kwargs)

    def ship_products(self, shipment, product_quantities, *args, **kwargs):
        if not self.modules:
            raise SupplierHasNoSupplierModules(
                "Cannot create shipments for this supplier as it has no supplier modules."
            )
        for module in self.modules:
            module.ship_products(shipment, product_quantities, *args, **kwargs)

    def soft_delete(self):
        if not self.deleted:
            self.deleted = True
            self.save(update_fields=("deleted",))


class SupplierShop(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_shops")
    shop = models.ForeignKey("shuup.Shop", on_delete=models.CASCADE, related_name="supplier_shops")
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_("Approved"),
        help_text=_("Indicates whether this supplier is currently approved for work."),
    )

    class Meta:
        unique_together = ("supplier", "shop")


class SupplierModule(models.Model):
    module_identifier = models.CharField(
        max_length=64,
        verbose_name=_("module identifier"),
        unique=True,
        help_text=_(
            "Select the types of products this supplier can handle."
            "Example for normal products select just Simple Supplier."
        ),
    )
    name = models.CharField(
        max_length=64,
        verbose_name=_("Module name"),
        help_text=_("Supplier modules name."),
    )

    def __str__(self):
        return self.name

    @classmethod
    def ensure_all_supplier_modules(cls):
        from shuup.apps.provides import get_provide_objects

        for module in get_provide_objects(Supplier.module_provides_key):
            cls.objects.update_or_create(module_identifier=module.identifier, defaults={"name": module.name})


SupplierLogEntry = define_log_model(Supplier)
