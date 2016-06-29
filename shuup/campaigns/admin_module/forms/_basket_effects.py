# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import PercentageField
from shuup.campaigns.models.basket_effects import (
    BasketDiscountAmount, BasketDiscountPercentage
)
from shuup.campaigns.models.basket_line_effects import (
    DiscountFromProduct, FreeProductLine
)

from ._base import BaseEffectModelForm


class BasketDiscountAmountForm(BaseEffectModelForm):
    class Meta(BaseEffectModelForm.Meta):
        model = BasketDiscountAmount


class BasketDiscountPercentageForm(BaseEffectModelForm):
    discount_percentage = PercentageField(
        max_digits=6, decimal_places=5,
        label=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."))

    class Meta(BaseEffectModelForm.Meta):
        model = BasketDiscountPercentage


class FreeProductLineForm(BaseEffectModelForm):
    class Meta(BaseEffectModelForm.Meta):
        model = FreeProductLine


class DiscountFromProductForm(BaseEffectModelForm):
    class Meta(BaseEffectModelForm.Meta):
        model = DiscountFromProduct
