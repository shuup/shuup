# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils import update_module_attributes

from ._context import TaxingContext
from ._line_tax import LineTax, SourceLineTax
from ._module import (
    get_tax_module, should_calculate_taxes_automatically, TaxModule
)
from ._price import TaxedPrice
from ._tax_summary import TaxSummary
from ._taxable import TaxableItem

__all__ = [
    "LineTax",
    "SourceLineTax",
    "TaxModule",
    "TaxSummary",
    "TaxableItem",
    "TaxedPrice",
    "TaxingContext",
    "get_tax_module",
    "should_calculate_taxes_automatically",
]

update_module_attributes(__all__, __name__)
