# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import TYPE_CHECKING, Union

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from jsonfield import JSONField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.core.modules import ModuleInterface
from shuup.utils.analog import define_log_model

from ._base import TranslatableShuupModel

if TYPE_CHECKING:
    from shuup.core.models import Shop


class SupplierType(Enum):
    INTERNAL = 1
    EXTERNAL = 2

    class Labels:
        INTERNAL = _('internal')
        EXTERNAL = _('external')


class SupplierQueryset(TranslatableQuerySet):
    def not_deleted(self):
        return self.filter(deleted=False)

    def enabled(self, shop: Union['Shop', int] = None):
        """
        Filter the queryset to contain only enabled and approved suppliers.

        If `shop` is given, only approved suppliers
        for the given shop will be filtered.

        `shop` can be either a Shop instance or the shop's PK
        """
        queryset = self.filter(
            enabled=True,
            supplier_shops__is_approved=True
        ).not_deleted()

        if shop:
            from shuup.core.models import Shop
            shop_id = shop.pk if isinstance(shop, Shop) else shop
            queryset = queryset.filter(supplier_shops__shop_id=shop_id)

        return queryset.distinct()


@python_2_unicode_compatible
class Supplier(ModuleInterface, TranslatableShuupModel):
    default_module_spec = "shuup.core.suppliers:BaseSupplierModule"
    module_provides_key = "supplier_module"

    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_('modified on'))
    identifier = InternalIdentifierField(unique=True)
    name = models.CharField(verbose_name=_("name"), max_length=128, db_index=True, help_text=_(
        "The product supplier's name. "
        "You can enable suppliers to manage the inventory of stocked products."
    ))
    type = EnumIntegerField(SupplierType, verbose_name=_("supplier type"), default=SupplierType.INTERNAL, help_text=_(
        "The supplier type indicates whether the products are supplied through an internal supplier or "
        "an external supplier, and which group this supplier belongs to."
    ))
    stock_managed = models.BooleanField(verbose_name=_("stock managed"), default=False, help_text=_(
        "Enable this if this supplier will manage the inventory of the stocked products. Having a managed stock "
        "enabled is unnecessary if e.g. selling digital products that will never run out no matter how many are "
        "being sold. There are some other cases when it could be an unnecessary complication. This setting"
        "merely assigns a sensible default behavior, which can be overwritten on a product-by-product basis."
    ))
    module_identifier = models.CharField(max_length=64, blank=True, verbose_name=_('module'), help_text=_(
        "Select the supplier module to use for this supplier. "
        "Supplier modules define the rules by which inventory is managed."
    ))
    module_data = JSONField(blank=True, null=True, verbose_name=_("module data"))

    shops = models.ManyToManyField(
        "Shop",
        blank=True,
        related_name="suppliers",
        verbose_name=_("shops"),
        help_text=_("You can select which particular shops fronts the supplier should be available in."),
        through="SupplierShop",
    )
    enabled = models.BooleanField(default=True, verbose_name=_("enabled"), help_text=_(
        "Indicates whether this supplier is currently enabled. In order to participate fully, "
        "the supplier also needs to be `Approved`."
    ))
    logo = FilerImageField(
        verbose_name=_("logo"),
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name="supplier_logos"
    )
    contact_address = models.ForeignKey(
        "MutableAddress",
        related_name="supplier_addresses",
        verbose_name=_("contact address"),
        blank=True, null=True,
        on_delete=models.SET_NULL
    )
    options = JSONField(blank=True, null=True, verbose_name=_("options"))
    translations = TranslatedFields(
        description=models.TextField(blank=True, verbose_name=_("description"))
    )
    slug = models.SlugField(
        verbose_name=_('slug'), max_length=255, blank=True, null=True,
        help_text=_(
            "Enter a URL slug for your supplier. Slug is user- and search engine-friendly short text "
            "used in a URL to identify and describe a resource. In this case it will determine "
            "what your supplier page URL in the browser address bar will look like. "
            "A default will be created using the supplier name."
        )
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

    def get_orderability_errors(self, shop_product, quantity, customer):
        """
        :param shop_product: Shop Product.
        :type shop_product: shuup.core.models.ShopProduct
        :param quantity: Quantity to order.
        :type quantity: decimal.Decimal
        :param contect: Ordering contact.
        :type contect: shuup.core.models.Contact
        :rtype: iterable[ValidationError]
        """
        return self.module.get_orderability_errors(shop_product=shop_product, quantity=quantity, customer=customer)

    def get_stock_statuses(self, product_ids):
        """
        :param product_ids: Iterable of product IDs.
        :return: Dict of {product_id: ProductStockStatus}
        :rtype: dict[int, shuup.core.stocks.ProductStockStatus]
        """
        return self.module.get_stock_statuses(product_ids)

    def get_stock_status(self, product_id):
        """
        :param product_id: Product ID.
        :type product_id: int
        :rtype: shuup.core.stocks.ProductStockStatus
        """
        return self.module.get_stock_status(product_id)

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
            for shop_product
            in self.shop_products.filter(shop=shop)
            if shop_product.is_orderable(self, customer, shop_product.minimum_purchase_quantity)
        ]

    def adjust_stock(self, product_id, delta, created_by=None, type=None):
        from shuup.core.suppliers.base import StockAdjustmentType
        adjustment_type = type or StockAdjustmentType.INVENTORY
        return self.module.adjust_stock(product_id, delta, created_by=created_by, type=adjustment_type)

    def update_stock(self, product_id):
        return self.module.update_stock(product_id)

    def update_stocks(self, product_ids):
        return self.module.update_stocks(product_ids)

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
        help_text=_("Indicates whether this supplier is currently approved for work.")
    )

    class Meta:
        unique_together = ("supplier", "shop")


SupplierLogEntry = define_log_model(Supplier)
