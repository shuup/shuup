# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.utils import update_module_attributes

from ._addresses import (
    ImmutableAddress, MutableAddress, SavedAddress, SavedAddressRole,
    SavedAddressStatus
)
from ._attributes import Attribute, AttributeType, AttributeVisibility
from ._base import (
    PolymorphicShoopModel, PolymorphicTranslatableShoopModel, ShoopModel,
    TranslatableShoopModel
)
from ._categories import Category, CategoryStatus, CategoryVisibility
from ._configurations import ConfigurationItem
from ._contacts import (
    AnonymousContact, CompanyContact, Contact, ContactGroup, Gender,
    get_person_contact, PersonContact
)
from ._counters import Counter, CounterType
from ._manufacturers import Manufacturer
from ._order_lines import OrderLine, OrderLineTax, OrderLineType
from ._orders import (
    Order, OrderLogEntry, OrderStatus, OrderStatusRole, PaymentStatus,
    ShippingStatus
)
from ._payments import Payment
from ._persistent_cache import PersistentCacheEntry
from ._product_media import ProductMedia, ProductMediaKind
from ._product_packages import ProductPackageLink
from ._product_shops import ProductVisibility, ShopProduct
from ._product_variation import (
    ProductVariationLinkStatus, ProductVariationResult,
    ProductVariationVariable, ProductVariationVariableValue
)
from ._products import (
    Product, ProductAttribute, ProductCrossSell, ProductCrossSellType,
    ProductMode, ProductType, ShippingMode, StockBehavior
)
from ._service_base import (
    Service, ServiceBehaviorComponent, ServiceChoice, ServiceCost,
    ServiceProvider
)
from ._service_behavior import (
    FixedCostBehaviorComponent, WaivingCostBehaviorComponent,
    WeightLimitsBehaviorComponent
)
from ._service_payment import (
    CustomPaymentProcessor, PaymentMethod, PaymentProcessor, PaymentUrls
)
from ._service_shipping import Carrier, CustomCarrier, ShippingMethod
from ._shipments import Shipment, ShipmentProduct
from ._shops import Shop, ShopStatus
from ._supplied_products import SuppliedProduct
from ._suppliers import Supplier, SupplierType
from ._taxes import CustomerTaxGroup, Tax, TaxClass
from ._units import SalesUnit

__all__ = [
    "AnonymousContact",
    "Attribute",
    "AttributeType",
    "AttributeVisibility",
    "Carrier",
    "Category",
    "CategoryStatus",
    "CategoryVisibility",
    "CompanyContact",
    "ConfigurationItem",
    "Contact",
    "ContactGroup",
    "Counter",
    "CounterType",
    "CustomCarrier",
    "CustomerTaxGroup",
    "CustomPaymentProcessor",
    "FixedCostBehaviorComponent",
    "get_person_contact",
    "Gender",
    "ImmutableAddress",
    "Manufacturer",
    "MutableAddress",
    "Order",
    "OrderLine",
    "OrderLineTax",
    "OrderLineType",
    "OrderLogEntry",
    "OrderStatus",
    "OrderStatusRole",
    "Payment",
    "PaymentMethod",
    "PaymentProcessor",
    "PaymentStatus",
    "PaymentUrls",
    "PersistentCacheEntry",
    "PersonContact",
    "PolymorphicShoopModel",
    "PolymorphicTranslatableShoopModel",
    "Product",
    "Product",
    "ProductAttribute",
    "ProductCrossSell",
    "ProductCrossSellType",
    "ProductMedia",
    "ProductMediaKind",
    "ProductMode",
    "ProductPackageLink",
    "ProductType",
    "ProductVariationLinkStatus",
    "ProductVariationResult",
    "ProductVariationVariable",
    "ProductVariationVariableValue",
    "ProductVisibility",
    "SalesUnit",
    "SavedAddress",
    "SavedAddressRole",
    "SavedAddressStatus",
    "Service",
    "ServiceBehaviorComponent",
    "ServiceChoice",
    "ServiceCost",
    "ServiceProvider",
    "Shipment",
    "ShipmentProduct",
    "ShippingMethod",
    "ShippingMode",
    "ShippingStatus",
    "ShoopModel",
    "Shop",
    "ShopProduct",
    "ShopStatus",
    "StockBehavior",
    "SuppliedProduct",
    "Supplier",
    "SupplierType",
    "Tax",
    "TaxClass",
    "TranslatableShoopModel",
    "WaivingCostBehaviorComponent",
    "WeightLimitsBehaviorComponent",
]

update_module_attributes(__all__, __name__)
