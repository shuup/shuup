# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from functools import lru_cache
from typing import Dict, Iterable

from shuup.apps.provides import get_provide_objects


class ProductKindSpec:
    """
    Specifies an product kind. Useful to
    control the visibility in admin module and also
    to control which supplier modules can handle it.
    """

    # The identifier of the product kind
    value = None  # type: int

    # The name of the product type that can be visible in the adin
    name = ""  # type: str

    # iterable of identifier of supplier modules
    # that support this product kind
    # if empty, it means any supplier module can handle it
    supported_supplier_modules = []  # type: Iterable[str]

    # Defines a name that will be used in admin
    # to list this product. Products with the same
    # listing name will be rendered in the same list.
    admin_listing_name = ""  # type: str

    @classmethod
    def get_enum_value_label(cls):
        return (cls.value, cls.name)


@lru_cache()
def get_product_kind_specs() -> Iterable[ProductKindSpec]:
    unique_values = []
    specs = []
    for product_kind_spec in get_provide_objects("product_kind_specs"):
        if product_kind_spec.value in unique_values:
            raise ValueError(_("The product kind {value} is not unique!").format(value=product_kind_spec.value))
        unique_values.append(product_kind_spec.value)
        specs.append(product_kind_spec)
    return specs


@lru_cache()
def get_product_kind_choices() -> Dict[int, str]:
    return [product_kind_spec.get_enum_value_label() for product_kind_spec in get_product_kind_specs()]


class DefaultProductKindSpec(ProductKindSpec):
    """
    The default product kind
    """

    value = 1
    name = _("Product")
    admin_listing_name = "products"
