# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.campaigns.models.catalog_filters import CategoryFilter, ProductFilter, ProductTypeFilter

from ._base import BaseRuleModelForm


class ProductTypeFilterForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = ProductTypeFilter


class ProductFilterForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = ProductFilter


class CategoryFilterForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = CategoryFilter
