# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from ._basket import BasketCampaignForm
from ._basket_conditions import (
    BasketMaxTotalAmountConditionForm,
    BasketMaxTotalProductAmountConditionForm, BasketTotalAmountConditionForm,
    BasketTotalProductAmountConditionForm, CategoryProductsBasketConditionForm,
    ContactBasketConditionForm, ContactGroupBasketConditionForm,
    ProductsInBasketConditionForm
)
from ._basket_effects import (
    BasketDiscountAmountForm, BasketDiscountPercentageForm,
    DiscountFromCategoryProductsForm, DiscountFromProductForm,
    FreeProductLineForm
)
from ._catalog import CatalogCampaignForm
from ._catalog_conditions import (
    ContactConditionForm, ContactGroupConditionForm
)
from ._catalog_effects import (
    ProductDiscountAmountForm, ProductDiscountPercentageForm
)
from ._catalog_filters import (
    CategoryFilterForm, ProductFilterForm, ProductTypeFilterForm
)
from ._coupon import CouponForm

__all__ = [
    "BasketCampaignForm",
    "BasketDiscountAmountForm",
    "BasketDiscountPercentageForm",
    "BasketMaxTotalAmountConditionForm",
    "BasketMaxTotalProductAmountConditionForm",
    "BasketTotalAmountConditionForm",
    "BasketTotalProductAmountConditionForm",
    "CatalogCampaignForm",
    "CategoryFilterForm",
    "CategoryProductsBasketConditionForm",
    "ContactBasketConditionForm",
    "ContactConditionForm",
    "ContactGroupBasketConditionForm",
    "ContactGroupConditionForm",
    "CouponForm",
    "DiscountFromCategoryProductsForm",
    "DiscountFromProductForm",
    "FreeProductLineForm",
    "ProductDiscountAmountForm",
    "ProductDiscountPercentageForm",
    "ProductFilterForm",
    "ProductsInBasketConditionForm",
    "ProductTypeFilterForm",
]
