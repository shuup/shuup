# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils import update_module_attributes

from ._addresses import (
    ImmutableAddress, MutableAddress, SavedAddress, SavedAddressRole,
    SavedAddressStatus
)
from ._attributes import Attribute, AttributeType, AttributeVisibility
from ._base import (
    PolymorphicShuupModel, PolymorphicTranslatableShuupModel, ShuupModel,
    TranslatableShuupModel
)
from ._basket import Basket
from ._categories import Category, CategoryStatus, CategoryVisibility
from ._configurations import ConfigurationItem
from ._contacts import (
    AnonymousContact, CompanyContact, CompanyContactLogEntry, Contact,
    ContactGroup, ContactGroupLogEntry, ContactGroupPriceDisplay, Gender,
    get_company_contact, get_company_contact_for_shop_staff,
    get_groups_for_price_display_create, get_person_contact,
    get_price_display_for_group_and_shop,
    get_price_display_options_for_group_and_shop, get_price_displays_for_shop,
    PersonContact, PersonContactLogEntry
)
from ._counters import Counter, CounterType
from ._currencies import Currency, get_currency_precision
from ._labels import Label
from ._manufacturers import Manufacturer
from ._media import MediaFile, MediaFolder
from ._order_lines import (
    AbstractOrderLine, OrderLine, OrderLineTax, OrderLineType
)
from ._orders import (
    DefaultOrderStatus, Order, OrderLogEntry, OrderStatus, OrderStatusManager,
    OrderStatusRole, PaymentStatus, ShippingStatus
)
from ._payments import AbstractPayment, Payment
from ._persistent_cache import PersistentCacheEntry
from ._product_media import ProductMedia, ProductMediaKind
from ._product_packages import ProductPackageLink
from ._product_shops import (
    ProductVisibility, ShopProduct, ShopProductVisibility
)
from ._product_variation import (
    get_all_available_combinations, ProductVariationLinkStatus,
    ProductVariationResult, ProductVariationVariable,
    ProductVariationVariableValue
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
    CountryLimitBehaviorComponent, FixedCostBehaviorComponent,
    GroupAvailabilityBehaviorComponent, OrderTotalLimitBehaviorComponent,
    RoundingMode, StaffOnlyBehaviorComponent, WaivingCostBehaviorComponent,
    WeightBasedPriceRange, WeightBasedPricingBehaviorComponent,
    WeightLimitsBehaviorComponent
)
from ._service_payment import (
    CustomPaymentProcessor, PaymentMethod, PaymentProcessor, PaymentUrls
)
from ._service_shipping import Carrier, CustomCarrier, ShippingMethod
from ._shipments import Shipment, ShipmentProduct, ShipmentStatus, ShipmentType
from ._shops import Shop, ShopStatus
from ._supplied_products import SuppliedProduct
from ._suppliers import Supplier, SupplierShop, SupplierType
from ._taxes import CustomerTaxGroup, Tax, TaxClass
from ._units import DisplayUnit, PiecesSalesUnit, SalesUnit, UnitInterface

__all__ = [
    "AbstractOrderLine",
    "AbstractPayment",
    "AnonymousContact",
    "Attribute",
    "AttributeType",
    "AttributeVisibility",
    "Basket",
    "Carrier",
    "Category",
    "CategoryStatus",
    "CategoryVisibility",
    "CompanyContact",
    "CompanyContactLogEntry",
    "ConfigurationItem",
    "Contact",
    "ContactGroup",
    "ContactGroupLogEntry",
    "ContactGroupPriceDisplay",
    "Counter",
    "CounterType",
    "CountryLimitBehaviorComponent",
    "CustomCarrier",
    "CustomerTaxGroup",
    "CustomPaymentProcessor",
    "Currency",
    "DefaultOrderStatus",
    "DisplayUnit",
    "FixedCostBehaviorComponent",
    "get_all_available_combinations",
    "get_company_contact",
    "get_company_contact_for_shop_staff",
    "get_currency_precision",
    "get_groups_for_price_display_create",
    "get_person_contact",
    "get_price_displays_for_shop",
    "get_price_display_for_group_and_shop",
    "get_price_display_options_for_group_and_shop",
    "Gender",
    "GroupAvailabilityBehaviorComponent",
    "ImmutableAddress",
    "Label",
    "Manufacturer",
    "MediaFile",
    "MediaFolder",
    "MutableAddress",
    "Order",
    "OrderLine",
    "OrderLineTax",
    "OrderLineType",
    "OrderLogEntry",
    "OrderStatus",
    "OrderStatusManager",
    "OrderStatusRole",
    "OrderTotalLimitBehaviorComponent",
    "Payment",
    "PaymentMethod",
    "PaymentProcessor",
    "PaymentStatus",
    "PaymentUrls",
    "PersistentCacheEntry",
    "PersonContact",
    "PersonContactLogEntry",
    "PiecesSalesUnit",
    "PolymorphicShuupModel",
    "PolymorphicTranslatableShuupModel",
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
    "RoundingMode",
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
    "ShipmentStatus",
    "ShipmentType",
    "ShippingMethod",
    "ShippingMode",
    "ShippingStatus",
    "ShuupModel",
    "Shop",
    "ShopProduct",
    "ShopProductVisibility",
    "ShopStatus",
    "StaffOnlyBehaviorComponent",
    "StockBehavior",
    "SuppliedProduct",
    "Supplier",
    "SupplierShop",
    "SupplierType",
    "Tax",
    "TaxClass",
    "TranslatableShuupModel",
    "UnitInterface",
    "WaivingCostBehaviorComponent",
    "WeightBasedPriceRange",
    "WeightBasedPricingBehaviorComponent",
    "WeightLimitsBehaviorComponent",
]

update_module_attributes(__all__, __name__)
